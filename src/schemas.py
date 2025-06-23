from pydantic import BaseModel, EmailStr, Field


class EmailBody(BaseModel):
    subject: str
    body: str
    recipients: list[EmailStr]
    subtype: str = "plain"
