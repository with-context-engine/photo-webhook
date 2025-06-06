"""
Agent module for classifying messages using BAML.
"""
from baml_client.async_client import b as async_b  # Async client
from baml_client.types import Message, Category
from typing import List, Any
from rich.console import Console
from memento.utils.logging import print_classification_panel, print_classification_error

async def classify_message_with_media(
    message_body: str
) -> Category:
    """
    Classify a message with optional text and images using BAML.
    
    Args:
        message_body: Optional text content of the message
        
    Returns:
        Category: The classified category of the message
    """
    # Prepare the input for BAML
    message_input = Message(
        message=message_body,
    )
    
    # Call the BAML function to classify the message
    try:
        category = await async_b.ConvertMessage(message_input)
        return category
    except Exception as e:
        print(f"Error classifying message: {e}")
        # Default to a fallback category if classification fails
        return Category.Ghibli

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
            print_classification_panel(console, classifications)
    except Exception as classification_error:
        category = "Ghibli"  # Fallback if classification fails
        print_classification_error(console, classification_error)
    
    return category
