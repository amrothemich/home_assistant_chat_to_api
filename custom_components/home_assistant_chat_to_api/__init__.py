"""The OpenAI Conversation integration."""
from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Literal

import aiohttp

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import intent
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.util import ulid

from .const import (
    CONF_API_URL,
    EVENT_CONVERSATION_FINISHED,
)

_LOGGER = logging.getLogger(__name__)

# Load manifest.json
with Path(__file__).parent.joinpath('manifest.json').open() as manifest_file:
    manifest = json.load(manifest_file)

__version__ = manifest['version']

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up OpenAI Conversation."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenAI Conversation from a config entry."""
    api_url = entry.data[CONF_API_URL]

    try:
        url = f"{api_url}/health"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ConnectionError("Unable to connect to API endpoint")
    except Exception as err:
        _LOGGER.error("Failed to connect to API endpoint: %s", err)
        return False

    agent = ExternalConversationAgent(hass, entry)
    conversation.async_set_agent(hass, entry, agent)
    return True

class ExternalConversationAgent(conversation.AbstractConversationAgent):
    """External conversation agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self.history: dict[str, list[dict]] = {}

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        if user_input.conversation_id in self.history:
            conversation_id = user_input.conversation_id
            messages = self.history[conversation_id]
        else:
            conversation_id = ulid.ulid()
            user_input.conversation_id = conversation_id
            messages = []

        # Add user message
        messages.append({
            "role": "user",
            "content": user_input.text
        })

        try:
            # Send messages to external API
            api_url = self.entry.data[CONF_API_URL]
            url = f"{api_url}/chat"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"messages": messages}) as response:
                    if response.status != 200:
                        raise ConnectionError(f"API request failed with status {response.status}")
                    
                    response_data = await response.json()
                    assistant_message = response_data.get("response", "")

            # Add assistant response to history
            messages.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            self.history[conversation_id] = messages

            self.hass.bus.async_fire(
                EVENT_CONVERSATION_FINISHED,
                {
                    "request": user_input.text,
                    "response": assistant_message,
                    "conversation_id": conversation_id,
                },
            )

            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(assistant_message)
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        except Exception as err:
            _LOGGER.error("Failed to process conversation: %s", err)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, I had a problem processing your request: {err}",
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

