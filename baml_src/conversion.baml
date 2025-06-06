class Message {
    message string
}

enum Category {
    Simpsons
    Ghibli
    ToyStory
    Pixar
    YayoiKusama
}

function ConvertMessage(input: Message) -> Category {
    client CustomGPT4o
    prompt #"
        Convert the following message into one of these categories:
        - Simpsons: Content related to The Simpsons TV show
        - Ghibli: Content related to Studio Ghibli movies/style
        - ToyStory: Content related to Toy Story movies
        - Pixar: Content related to other Pixar movies (excluding Toy Story)
        - YayoiKusama: Content related to Yayoi Kusama's art style (polka dots, infinity rooms, etc.)
        
        {% if input.message %}
        Text message: {{ input.message }}
        {% endif %}

        Analyze the text (if provided) to determine which category best fits the content.
        
        {{ ctx.output_format }}
    "#
}

test ConvertMessage {
    functions [ConvertMessage]
    args {
        input {
            message "Can you convert this image into Studio Ghibli format?"
        }
    }
}