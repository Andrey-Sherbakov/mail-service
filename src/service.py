import json
from dataclasses import dataclass

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from fastapi_mail import MessageSchema, FastMail
from pydantic import EmailStr

from src.broker.producer import BrokerProducer
from src.config import Settings
from src.schemas import EmailBody


@dataclass
class MailService:
    settings: Settings
    broker_producer: BrokerProducer

    async def consume_message(self, message: AbstractIncomingMessage) -> None:
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
        await self.broker_producer.publish(message=message)
        print("Callback sent")

    async def send_email(self, email_body: EmailBody) -> None:
        message = MessageSchema(**email_body.model_dump())
        fm = FastMail(self.settings.MAIL_CONFIG)
        await fm.send_message(message=message)
        print("Email sent")


async def get_mail_service(settings: Settings, broker_producer: BrokerProducer) -> MailService:
    return MailService(settings=settings, broker_producer=broker_producer)
