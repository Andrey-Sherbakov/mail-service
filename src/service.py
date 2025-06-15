from dataclasses import dataclass

from fastapi_mail import MessageSchema, FastMail
from pydantic import EmailStr, ValidationError

from src.broker.producer import BrokerProducer
from src.config import Settings
from src.schemas import EmailBody, EmailCallbackBody


@dataclass
class MailService:
    settings: Settings
    broker_producer: BrokerProducer

    async def consume_message(self, message: dict) -> None:
        email_body = EmailBody(**message)
        try:
            await self.send_email(email_body=email_body)
            print("Email sent")
        except Exception as e:
            await self.send_fail_callback(
                recipients=email_body.recipients,
                correlation_id=email_body.correlation_id,
                exception=e,
            )
            print("Email failed with exception:", e)

    async def send_fail_callback(
        self, recipients: list[EmailStr], correlation_id: str, exception: Exception
    ) -> None:
        message = EmailCallbackBody(
            message=f"Failed to send email to {recipients}: {exception}",
            correlation_id=correlation_id,
        )
        await self.broker_producer.send_mail(message=message.model_dump())

    async def send_email(self, email_body: EmailBody) -> None:
        message = MessageSchema(**email_body.model_dump())
        fm = FastMail(self.settings.MAIL_CONFIG)
        await fm.send_message(message=message)


async def get_mail_service(settings: Settings, broker_producer: BrokerProducer) -> MailService:
    return MailService(settings=settings, broker_producer=broker_producer)
