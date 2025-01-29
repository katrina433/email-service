import re

from pydantic import BaseModel, Field, field_validator


class Nonprofit(BaseModel):
    email_address: str = Field(examples=["test@email.com"])
    name: str = Field(examples=["Test Name"])
    address: str = Field(examples=["Test Street, New York, NY"])


class Email(BaseModel):
    sender: str = Field(examples=["sender@email.com"])
    recipients: list[str] = Field(examples=[["test@email.com"]])
    cc: list[str] = Field(examples=[["test@email.com"]])
    bcc: list[str] = Field(examples=[["test@email.com"]])
    subject: str = Field(examples=["Email Subject"])
    content: str = Field(examples=["Email Content......"])


class TemplatedEmail(Email):
    subject: str = Field(examples=["Email Subject to {name}"])
    content: str = Field(examples=["Email Content to {name} at {address}"])

    @field_validator("subject", "content")
    def valid_template(s: str) -> str:
        params = re.findall(r"{([^}]+)}", s)
        for param in params:
            if param not in Nonprofit.model_fields:
                raise ValueError(f"bad param {param}")
        return s
