from pydantic import BaseModel, EmailStr


class EmailBody(BaseModel):
    subject: str
    body: str
    recipients: list[EmailStr]
    subtype: str = "plain"
