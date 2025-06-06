import modal
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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
                
                # Create Rich console
                console = Console()
                
                # Create message info table
                message_table = Table(show_header=False, box=None)
                message_table.add_row("From", f"{message_data.conversation.contact.first_name} {message_data.conversation.contact.last_name}")
                message_table.add_row("Phone", message_data.conversation.contact.phone_number)
                message_table.add_row("Message", message_data.body)
                message_table.add_row("Received at", message_data.received_at)
                
                # Create attachments table if there are any
                if message_data.attachments:
                    attachments_table = Table(show_header=True, header_style="bold magenta")
                    attachments_table.add_column("Type")
                    attachments_table.add_column("URL")
                    for attachment in message_data.attachments:
                        attachments_table.add_row(attachment.type, attachment.url)
                else:
                    attachments_table = None
                
                # Print message received panel
                console.print(Panel(
                    message_table,
                    title="[bold blue]MESSAGE RECEIVED[/]",
                    border_style="blue"
                ))
                
                # Print attachments if any
                if message_data.attachments and attachments_table:
                    console.print(Panel(
                        attachments_table,
                        title="[bold magenta]ATTACHMENTS[/]",
                        border_style="magenta"
                    ))
                else:
                    console.print(Panel(
                        Text("No attachments", style="bold red"),
                        title="[bold red]NO ATTACHMENTS[/]",
                        border_style="red"
                    ))

                # Classify the message and its attachments
                classification = await classify_message_and_attachments(
                    message_body=message_data.body or "",
                    attachments=message_data.attachments,
                    console=console
                )
                
                # Store message in Convex database
                try:
                    convex_result = await store_message_in_convex(message_data, webhook_payload.account_id, classification)
                    print(f"Successfully stored message in Convex: {convex_result}")
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

async def classify_message_and_attachments(
    message_body: str,
    attachments: List[Any],
    console: Console
) -> str:
    """
    Classify a message and its attachments, handling any errors gracefully.
    
    Args:
        message_body: The text content of the message
        attachments: List of message attachments
        console: Rich console instance for logging
        
    Returns:
        str: The classification category (either from classification or fallback "Ghibli")
    """
    category = None
    try:
        category = await classify_message_with_media(
            message_body=message_body or ""
        )
        for attachment in attachments:
            if attachment.type.startswith('image'):
                attachment.classification = category
            else:
                attachment.classification = "Ghibli"

        # Print classification result for all images
        if any(a.type.startswith('image') for a in attachments):
            classifications = [
                f"{a.url}: {category}" for a in attachments if a.type.startswith('image')
            ]
            console.print(Panel(
                Text("\n".join(classifications), style="bold green"),
                title="[bold green]IMAGE CLASSIFICATIONS[/]",
                border_style="green"
            ))
    except Exception as classification_error:
        category = "Ghibli"  # Fallback if classification fails
        console.print(Panel(
            Text(f"Error classifying message: {classification_error}", style="bold red"),
            title="[bold red]CLASSIFICATION ERROR[/]",
            border_style="red"
        ))
    
    return category

