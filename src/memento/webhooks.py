import modal
from typing import Dict, Any, Optional, List

###
# Constants
###

MINUTE = 60  # seconds
HOUR = MINUTE * 60

###
# Image
###

webhook_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi>=0.115.12",
        "pydantic>=2.11.5", 
        "python-dotenv>=1.1.0",
        "convex>=0.7.0",
    )
)

###
# Imports
###

with webhook_image.imports():
    import os
    from datetime import datetime
    from dotenv import load_dotenv
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    from convex import ConvexClient

###
# App
###

app = modal.App(name="memento-surge-webhooks")

###
# Pydantic Models
###

class Attachment(BaseModel):
    id: str
    type: str
    url: str

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



###
# FastAPI App
###

@app.function(
    image=webhook_image,
    secrets=[modal.Secret.from_name("memento-secrets-dev"), modal.Secret.from_name("memento-secrets"), modal.Secret.from_name("memento-secrets-dev-convex")],
    max_containers=10,
    scaledown_window=MINUTE * 5
)
@modal.asgi_app(label="surge-webhooks")
def webhook_application():
    load_dotenv()

    # Create FastAPI app
    web_app = FastAPI(
        title="Memento Surge Webhook Handler", 
        version="0.1.0",
        description="Webhook handler for Surge SMS messages"
    )

    @web_app.get("/")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "memento-webhook-handler"}

    @web_app.post("/webhooks/surge")
    async def handle_surge_webhook(
        request: Request,
    ):
        """
        Handle incoming webhooks from Surge.
        Currently processes message.received events and prints confirmation.
        """
        try:
            # Parse the webhook payload
            payload_data = await request.json()
            
            # Validate payload structure
            try:
                webhook_payload = MessageReceivedPayload(**payload_data)
            except Exception as e:
                print(f"Invalid webhook payload structure: {e}")
                raise HTTPException(status_code=400, detail="Invalid payload structure")
            
            # Handle message.received events
            if webhook_payload.type == "message.received":
                message_data = webhook_payload.data
                
                # Print message received confirmation
                print("=" * 50)
                print("MESSAGE RECEIVED")
                print("=" * 50)
                print(f"From: {message_data.conversation.contact.first_name} {message_data.conversation.contact.last_name}")
                print(f"Phone: {message_data.conversation.contact.phone_number}")
                print(f"Message: {message_data.body}")
                print(f"Received at: {message_data.received_at}")
                
                if message_data.attachments:
                    print(f"Attachments: {len(message_data.attachments)}")
                    for attachment in message_data.attachments:
                        print(f"  - {attachment.type}: {attachment.url}")
                
                print("=" * 50)
                
                # Store message in Convex database
                try:
                    convex_result = await store_message_in_convex(message_data, webhook_payload.account_id)
                    print(f"Successfully stored message in Convex: {convex_result}")
                except Exception as convex_error:
                    print(f"Error storing message in Convex: {convex_error}")
                    # Continue processing even if Convex storage fails
                
                return JSONResponse(
                    status_code=200,
                    content={"status": "success", "message": "Webhook processed successfully"}
                )
            
            else:
                print(f"Received unhandled webhook type: {webhook_payload.type}")
                return JSONResponse(
                    status_code=200,
                    content={"status": "ignored", "message": f"Webhook type {webhook_payload.type} not handled"}
                )
        
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error processing webhook: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    return web_app

async def store_message_in_convex(message_data: MessageData, account_id: str):
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
