class Message {
    message string
}

class MessageWithImage {
    message string?
    image_urls string[]
}

enum Category {
    Simpsons
    Ghibli
    ToyStory
    Pixar
    YayoiKusama
}

function ConvertMessage(message: Message) -> Category {
    client "openai/gpt-4o"
    prompt #"
        Classify the following message into a category:
        {{ _.role("user") }} {{ message.message }}
        
        {{ ctx.output_format }}
    "#
}

function ClassifyMessageWithMedia(input: MessageWithImage) -> Category {
    client CustomGPT4o
    prompt #"
        Classify the following message and/or image(s) into one of these categories:
        - Simpsons: Content related to The Simpsons TV show
        - Ghibli: Content related to Studio Ghibli movies/style
        - ToyStory: Content related to Toy Story movies
        - Pixar: Content related to other Pixar movies (excluding Toy Story)
        - YayoiKusama: Content related to Yayoi Kusama's art style (polka dots, infinity rooms, etc.)
        
        {% if input.message %}
        Text message: {{ input.message }}
        {% endif %}
        
        {% if input.image_urls %}
        {% for image_url in input.image_urls %}
        ![Image {{ loop.index }}]({{ image_url }})
        {% endfor %}
        {% endif %}
        
        Analyze both the text (if provided) and images (if provided) to determine which category best fits the content.
        
        {{ ctx.output_format }}
    "#
}

test ConvertMessage {
    functions [ConvertMessage]
    args {
        message {
            message #"
                Can you convert this image into Studio Ghibli format? 
            "#
        }
    }
}

test ClassifyMessageWithMedia {
    functions [ClassifyMessageWithMedia]
    args {
        input {
            message "Can you convert this image into Studio Ghibli format?"
            image_urls ["https://example.com/image.jpg"]
        }
    }
}