from pydantic import BaseModel, EmailStr, Field


class EmailBody(BaseModel):
    subject: str
    body: str = Field(alias="message")
    recipients: list[EmailStr]
    subtype: str = "plain"
