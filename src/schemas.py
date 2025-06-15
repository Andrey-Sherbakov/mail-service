from pydantic import BaseModel, EmailStr, Field


class EmailBody(BaseModel):
    correlation_id: str
    subject: str
    body: str
    recipients: list[EmailStr]
    subtype: str = "plain"


class EmailCallbackBody(BaseModel):
    correlation_id: str
    message: str
