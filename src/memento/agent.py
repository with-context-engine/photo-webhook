"""
Agent module for classifying messages using BAML.
"""
from typing import List, Optional
from baml_client.async_client import b as async_b  # Async client
from baml_client.types import MessageWithImage, Category


async def classify_message_with_media(
    message_body: Optional[str] = None,
    attachment_urls: Optional[List[str]] = None
) -> Category:
    """
    Classify a message with optional text and images using BAML.
    
    Args:
        message_body: Optional text content of the message
        attachment_urls: Optional list of image URLs from attachments
        
    Returns:
        Category: The classified category of the message
    """
    # Prepare the input for BAML
    message_input = MessageWithImage(
        message=message_body,
        image_urls=attachment_urls or []
    )
    
    # Call the BAML function to classify the message
    try:
        category = await async_b.ClassifyMessageWithMedia(message_input)
        print(f"Message classified as: {category}")
        return category
    except Exception as e:
        print(f"Error classifying message: {e}")
        # Default to a fallback category if classification fails
        return Category.Ghibli
