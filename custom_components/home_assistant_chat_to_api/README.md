# Home Assistant Chat to API Integration

A Home Assistant integration that allows you to chat with any API endpoint using the Home Assistant conversation interface.

## Features

- Integrates with Home Assistant's native conversation interface
- Supports any API endpoint that follows a simple chat protocol
- Maintains conversation history
- Easy configuration through the UI

## Installation

1. Install through HACS by adding this repository (https://github.com/aaroncasey/home_assistant_chat_to_api)
2. Restart Home Assistant
3. Add the integration through the Home Assistant UI (Settings -> Devices & Services -> Add Integration -> Chat to API)
4. Configure your API endpoint URL

## Configuration

The integration requires the following:

- API URL: The URL of your chat API endpoint (e.g., http://localhost:5000)

The API endpoint should:
- Accept POST requests to `/chat` with a JSON body containing `messages`
- Return responses in JSON format with a `response` field
- Have a `/health` endpoint that returns 200 OK when healthy

## API Protocol

### Chat Endpoint (/chat)

Request format:
```json
{
    "messages": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]
}
```

Response format:
```json
{
    "response": "I'm doing well, thank you for asking!"
}
```

## Support

For bugs and feature requests, please open an issue on GitHub. 