import modal
from rich.console import Console

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
        "rich"
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
    from memento.agent import classify_message_and_attachments
    from memento.types.types import MessageReceivedPayload
    from memento.utils.convex import store_message_in_convex
    from memento.utils.logging import build_message_table, build_attachments_table, print_message_panel, print_attachments_panel, print_convex_result_panel

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

    @web_app.get("/")
    async def root():
        return {"message": "Memento Surge Webhook Handler is running"}

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
                
                # Create Rich console
                console = Console()
                
                # Build tables using logging utils
                message_table = build_message_table(message_data)
                attachments_table = build_attachments_table(message_data.attachments)
                
                # Print message received panel
                print_message_panel(console, message_table)
                
                # Print attachments panel
                print_attachments_panel(console, attachments_table)

                # Classify the message and its attachments
                classification = await classify_message_and_attachments(
                    message_body=message_data.body or "",
                    attachments=message_data.attachments,
                    console=console
                )

                # Future: Check if the user has credits or has made a payment to allow this action

                # If the user has credits, allow the OpenAI API to convert the attachment to a new image mode and upload to Convex
                
                # Store message, original attachments, conversion from OpenAI, and classification in Convex
                try:
                    convex_result = await store_message_in_convex(message_data, webhook_payload.account_id, classification)
                    print_convex_result_panel(console, convex_result)
                except Exception as convex_error:
                    print(f"Error storing message in Convex: {convex_error}")
                
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