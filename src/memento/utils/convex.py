from memento.types.types import MessageData
import os
from convex import ConvexClient
from typing import Optional

async def store_message_in_convex(message_data: MessageData, account_id: str, classification: Optional[str] = None):
    """
    Store message data in Convex database using the storeMessage mutation.
    """
    CONVEX_URL = os.getenv("CONVEX_URL")
    
    if not CONVEX_URL:
        raise ValueError("CONVEX_URL is not set in secrets")
        
    client = ConvexClient(CONVEX_URL)
    
    # Prepare attachments data
    attachments = []
    for attachment in message_data.attachments:
        attachments.append({
            "attachmentId": attachment.id,
            "type": attachment.type,
            "url": attachment.url,
            "classification": classification,
        })
    
    # Prepare the arguments for the Convex mutation (simplified to match expected format)
    mutation_args = {
        "messageId": message_data.id,
        "messageBody": message_data.body,
        "accountId": account_id,
        "receivedAt": message_data.received_at,
        "contactId": message_data.conversation.contact.id,
        "contactPhoneNumber": message_data.conversation.contact.phone_number,
        "conversationId": message_data.conversation.id,
        "phoneNumberId": message_data.conversation.phone_number.id,
        "phoneNumber": message_data.conversation.phone_number.number,
        "phoneNumberType": message_data.conversation.phone_number.type,
        "attachments": attachments,
    }
    
    # Call the Convex mutation
    result = client.mutation("messages:storeMessage", mutation_args)
    
    return result