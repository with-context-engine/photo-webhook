from fastapi import Body
import modal
from pdf2image import convert_from_bytes
from pydantic import BaseModel
    
###
# Constants
###

MINUTE = 60 # seconds
HOUR = MINUTE * 60
DAY = HOUR * 24

###
# Image
###

asgi_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("poppler-utils")
    .pip_install(
        "httpx>=0.28.1",
        "pydantic>=2.11.1",
        "python-dotenv>=1.1.0",
        "starlette>=0.41.0",
        "markdown>=3.5.1",
        "fastapi",
        "pdf2image",
        "pillow",
        "google-genai"
    )
    .add_local_file(
        local_path="./HTML.md",
        remote_path="/root/HTML.md",
    )
)

application_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("poppler-utils")
    .add_local_python_source(
        "rebuild",
        copy=True,
    )
    .pip_install(
        "mirascope[openai]",
        "mirascope[mistral]",
        "mirascope[google]",
        "mirascope[gemini]",
        "mirascope[anthropic]",
        "pydantic>=2.11.1",
        "fastapi",
        "pdf2image",
        "pillow",
        "httpx>=0.28.1",
        "google-genai"
    )
)

###
# Imports
### 

with application_image.imports():
    from rebuild.utils.vision import create_vision_function, process_images_with_vision
    from rebuild.utils.data import get_data_url, download_pdf
    from rebuild.utils.postprocessing import process_extraction_result, consolidate_extraction_results
    from rebuild.schema.extraction import ExtractionResult
    from pdf2image import convert_from_bytes

with asgi_image.imports():
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    import markdown
    import json
    from rebuild.schema.extraction import ExtractionResult

###
# App
###

app = modal.App(name="rebuild-ocr-v2")

####
# Mirascope Function
### 

@app.cls(
        image=application_image,
        scaledown_window=MINUTE * 10,
        secrets=[
            modal.Secret.from_name("rebuild-ocr-secrets"),
            modal.Secret.from_name("anthropic-secret"),
            modal.Secret.from_name("mistral-ocr-secret"),
            modal.Secret.from_name("google-api-secret")
        ]
)
class RebuildVision:
    @modal.method()
    async def extract(
        self,
        url: str,
        provider: str = 'openai',
        media_type: str = "application/pdf",
        model: str = "gpt-4o",
        max_concurrent: int = 5,
        prompt: str = "Extract the information from the image. Focus only on the shorthand annotations and the text. Do not include any descriptor information. Concatenate any lines output that are just blank.",
    ):
        # Handle PDFs differently from regular images
        if media_type == "application/pdf":
            # Download PDF
            pdf_content = await download_pdf(url)
            # Convert to images
            images = convert_from_bytes(pdf_content)
            # Create vision function
            vision_func = create_vision_function(provider)
            # Process images concurrently
            results = await process_images_with_vision(
                images=images,
                vision_function=vision_func,
                max_concurrency=max_concurrent,
                media_type=media_type,
                prompt=prompt
            )
            return consolidate_extraction_results(
                results=results,
                file=url.split('/')[-1],
                url=url,
                media_type=media_type,
                provider=provider,
                model=model,
                prompt=prompt
            ).model_dump_json(indent=4)
        else:
            raise ValueError(f"Unsupported media type: {media_type}")

### 
# FastAPI
###

# Request model
class ExtractionRequest(BaseModel):
    url: str
    provider: str = 'openai'
    media_type: str = "application/pdf"
    model: str = "gpt-4o"
    max_concurrent: int = 20
    prompt: str = "Extract the information from the image. Focus only on the shorthand annotations and the text. Do not include any descriptor information. Concatenate any lines output that are just blank."
@app.function(
    image=asgi_image,
    max_containers=20
)
@modal.asgi_app(label="rebuild-vision")
def vision_application():
    web_application = FastAPI(title="Rebuild OCR V2", description="Extract information from images")

    # Extract endpoint
    @web_application.post("/extract", response_model=ExtractionResult)
    async def extract(
        request: ExtractionRequest = Body(...)
    ):
        vision = RebuildVision()
        result_json = vision.extract.remote(
            url=request.url,
            provider=request.provider,
            media_type=request.media_type,
            model=request.model,
            max_concurrent=request.max_concurrent,
            prompt=request.prompt
        )
        return json.loads(result_json)

    # Root endpoint
    @web_application.get("/")
    def root():
        try:
            with open("/root/HTML.md", "r") as f:
                content = f.read()
            html_content = markdown.markdown(content, extensions=["tables"])
            html_page = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Rebuild OCR</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    h1, h2, h3 {{ color: #2c3e50; }}
                    code {{ background-color: #f8f8f8; padding: 2px 4px; border-radius: 3px; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            return HTMLResponse(content=html_page, status_code=200)
        except FileNotFoundError:
            return HTMLResponse(content="README.md not found", status_code=404)
        except Exception as e:
            return HTMLResponse(content=f"Error: {str(e)}", status_code=500)
        
    return web_application