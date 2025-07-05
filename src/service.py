import json
from dataclasses import dataclass

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from fastapi import FastAPI
from fastapi_mail import MessageSchema, FastMail

from src.broker.producer import BrokerProducer
from src.logger import logger
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
                await self.send_email(email_body=email_body, correlation_id=correlation_id)
                await self.send_success_callback(correlation_id=correlation_id)
            except Exception as e:
                logger.error(
                    f"Failed to send email: subject={email_body.subject}, "
                    f"to={email_body.recipients}, exception={e}, correlation_id={correlation_id}"
                )
                await self.send_fail_callback(
                    correlation_id=correlation_id,
                    exception=e,
                )

    async def send_success_callback(self, correlation_id: str) -> None:
        message = aio_pika.Message(
            body="Email send successfully".encode(),
            correlation_id=correlation_id,
        )
        await self.broker_producer.publish(message=message)

    async def send_fail_callback(self, correlation_id: str, exception: Exception) -> None:
        message = aio_pika.Message(
            body=f"Failed to send email with exception={exception}".encode(),
            correlation_id=correlation_id,
        )
        await self.broker_producer.publish(message=message)

    async def send_email(self, email_body: EmailBody, correlation_id: str) -> None:
        message = MessageSchema(**email_body.model_dump())
        fm = FastMail(self.settings.MAIL_CONFIG)
        await fm.send_message(message=message)
        logger.info(
            f"Email send: subject={email_body.subject}, to={email_body.recipients}, "
            f"correlation_id={correlation_id}"
        )


async def setup_mail_service(app: FastAPI):
    app.state.mail_service = MailService(
        settings=app.state.settings, broker_producer=app.state.broker_producer
    )
