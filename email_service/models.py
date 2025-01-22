from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from email_service.database import Base


class Nonprofit(Base):
    __tablename__ = "nonprofit"

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    email_address = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255))
    emails = relationship("EmailRecipient", backref="recipient", cascade="all,delete")
    
class Email(Base):
    __tablename__ = "email"

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    id = Column(Integer, primary_key=True)
    sender = Column(String(50), nullable=False)
    subject = Column(String(255))
    content = Column(String(5000))
    recipients = relationship("EmailRecipient", backref="email", cascade="all,delete", lazy="joined")

class EmailRecipient(Base):
    __tablename__ = "email_receipient"

    email_id = Column(Integer, ForeignKey("email.id", ondelete="CASCADE"), primary_key=True)
    email_address = Column(String(50), ForeignKey("nonprofit.email_address", ondelete="CASCADE"), primary_key=True)
