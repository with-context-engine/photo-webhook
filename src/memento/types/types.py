

###
# Pydantic Models
###

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from pydantic import BaseModel


class Attachment(BaseModel):
    id: str
    type: str
    url: str
    classification: Optional[str] = None

class Contact(BaseModel):
    id: str
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: str
    metadata: Dict[str, Any] = {}

class PhoneNumber(BaseModel):
    id: str
    number: str
    type: str

class Conversation(BaseModel):
    contact: Contact
    id: str
    phone_number: PhoneNumber

class MessageData(BaseModel):
    attachments: List[Attachment] = []
    body: Optional[str] = None
    conversation: Conversation
    id: str
    received_at: str

class MessageReceivedPayload(BaseModel):
    account_id: str
    type: str = Field(..., pattern="^message\\.received$")
    data: MessageData
