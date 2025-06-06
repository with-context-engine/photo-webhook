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
        "baml-py>=0.89.0",
    )
    .add_local_python_source("memento")
    .add_local_dir("baml_client", "/root/baml_client")
    .add_local_dir("baml_src", "/root/baml_src")
)

###
# Imports
###

with webhook_image.imports():
    from dotenv import load_dotenv
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    from memento.agent import classify_message_with_media
    from memento.types.types import MessageReceivedPayload
    from memento.utils.convex import store_message_in_convex

###
# Modal App
###

app = modal.App(name="memento-surge-webhooks")

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
                
                # Classify the message using BAML
                try:
                    # Extract image URLs from attachments (only image types)
                    image_urls = [
                        attachment.url 
                        for attachment in message_data.attachments 
                        if attachment.type.startswith('image')
                    ]
                    
                    # Classify the message
                    category = await classify_message_with_media(
                        message_body=message_data.body,
                        attachment_urls=image_urls if image_urls else None
                    )
                    
                    print(f"CLASSIFICATION: {category}")
                    print("=" * 50)
                    
                except Exception as classification_error:
                    print(f"Error classifying message: {classification_error}")
                    category = None
                
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

