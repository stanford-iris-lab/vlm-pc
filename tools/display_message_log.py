import json
import pdfkit

def extract_messages_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def save_chat_to_pdf(messages, output_path):
    chat_html = """
    <style>
        .chat-container {
            font-family: Arial, sans-serif;
            margin: 0 auto;
            max-width: 600px;
            padding: 20px;
        }
        .user-message, .assistant-message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 10px;
            word-wrap: break-word;
        }
        .user-message {
            background-color: #e0f7fa;
            text-align: right;
        }
        .assistant-message {
            background-color: #f1f8e9;
            text-align: left;
        }
        .message-content img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 10px 0;
        }
    </style>
    <div class="chat-container">
    """
    for message in messages:
        content = message['content']

        if isinstance(content, str):
            content_html = content
        else:
            if len(content) == 1:
                if content[0]['type'] == "text":
                    content_html = content[0]["text"]
                if content[0]['type'] == 'image_url':
                    image_url = content[0]['image_url']["url"]
                    content_html = f'<div class="message-content"><img src="{image_url}" alt="Image"></div>'
            else:
                for content_element in content:
                    if content_element['type'] == "text":
                        content_html = content_element["text"]
                        
                
                # Check for embedded image tags
                for content_element in content:
                    if content_element['type'] == "image_url":
                        image_url = content_element['image_url']["url"]
                        content_html += f'<div class="message-content"><img src="{image_url}" alt="Image"></div>'

        if message['role'] == 'user':
            chat_html += f'<div class="user-message">{content_html}</div>'
        elif message['role'] == 'assistant':
            chat_html += f'<div class="assistant-message">{content_html}</div>'
    chat_html += "</div>"
    
    # Save the HTML to a PDF file
    pdfkit.from_string(chat_html, output_path)


# Example messages for demonstration

