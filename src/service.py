import json
from dataclasses import dataclass

import aio_pika
from aio_pika.abc import AbstractRobustChannel
from fastapi_mail import MessageSchema, FastMail
from pydantic import EmailStr

from src.config import Settings
from src.schemas import EmailBody


@dataclass
class MailService:
    settings: Settings
    channel: AbstractRobustChannel

    async def consume_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process():
            email_body = EmailBody(**json.loads(message.body.decode()))
            correlation_id = message.correlation_id

            try:
                await self.send_email(email_body=email_body)
            except Exception as e:
                await self.send_fail_callback(
                    recipients=email_body.recipients, correlation_id=correlation_id, exception=e
                )

    async def send_fail_callback(
        self, recipients: list[EmailStr], correlation_id: str, exception: Exception
    ) -> None:
        message = aio_pika.Message(
            body=f"Failed to send email to {recipients}: {exception}".encode(),
            correlation_id=correlation_id,
        )
        await self.channel.default_exchange.publish(
            message=message, routing_key=self.settings.BROKER_CALLBACK_ROUTING_KEY
        )

    async def send_email(self, email_body: EmailBody) -> None:
        message = MessageSchema(**email_body.model_dump())

        fm = FastMail(self.settings.MAIL_CONFIG)
        await fm.send_message(message=message)


async def get_mail_service(settings: Settings, channel: AbstractRobustChannel) -> MailService:
    return MailService(settings=settings, channel=channel)
