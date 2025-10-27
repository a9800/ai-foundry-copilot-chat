from __future__ import annotations

from os import environ
from typing import Optional

import json
from dotenv import load_dotenv
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory

from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
    StoreItem,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalConnectionManager

from microsoft_agents.activity import Attachment, load_configuration_from_env, Activity

from src.agent import InventoryDeliveryAgent

load_dotenv()
agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT = InventoryDeliveryAgent(
    AzureChatCompletion(
        api_version=environ["AZURE_OPENAI_API_VERSION"],
        endpoint=environ["AZURE_OPENAI_ENDPOINT"],
        api_key=environ["AZURE_OPENAI_API_KEY"],
        deployment_name=environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
    )
)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)

class ChatHistoryStoreItem(StoreItem):

    def __init__(self, chat_history: Optional[ChatHistory] = None):
        self.chat_history = chat_history or ChatHistory()

    def store_item_to_json(self) -> dict:
        return self.chat_history.model_dump()
        
    @staticmethod
    def from_json_to_store_item(json_data: dict) -> ChatHistoryStoreItem:
        chat_history = ChatHistory.model_validate(json_data)
        return ChatHistoryStoreItem(chat_history)


@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    members_added = context.activity.members_added
    for member in members_added:
        if member.id != context.activity.recipient.id:
            await context.send_activity("Hello and welcome!")


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    try:
        chat_history_store_item = state.get_value(
            "ConversationState.chatHistory", lambda: ChatHistoryStoreItem(), target_cls=ChatHistoryStoreItem
        )

        forecast_response = await AGENT.invoke_agent(context.activity.text, chat_history_store_item.chat_history)

        state.set_value("ConversationState.chatHistory", chat_history_store_item)

        if forecast_response is None:
            await context.send_activity("Sorry, I couldn't get the weather forecast at the moment.")
        elif forecast_response.contentType == "AdaptiveCard":
            # Create an activity with attachment for adaptive cards
            activity = Activity(
                type="message",
                attachments=[
                    Attachment(
                        content_type="application/vnd.microsoft.card.adaptive",
                        content=forecast_response.content,
                    )
                ]
            )
            await context.send_activity(activity)
        else:
            await context.send_activity(forecast_response.content)
            
    except Exception as e:
        print(f"Error in on_message: {e}")
        await context.send_activity("Sorry, I encountered an error processing your request.")