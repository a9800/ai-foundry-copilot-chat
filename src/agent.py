import json
from typing import Union, Literal, Any

from pydantic import BaseModel

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread

from src.plugins import DateTimePlugin, AdaptiveCardPlugin
from src.plugins.inventory_plugin import InventoryManagementPlugin
from src.plugins.delivery_plugin import DeliveryManagementPlugin


class InventoryDeliveryAgentResponse(BaseModel):
    contentType: str = Literal["Text", "AdaptiveCard"]
    content: Union[dict, str]


class InventoryDeliveryAgent:

    agent_name = "InventoryDeliveryAgent"

    agent_instructions = """
            You are a helpful inventory and delivery management agent for a retail chain. You help store managers and employees with:

            **Inventory Management:**
            - Check current stock levels for any store and SKU
            - Monitor low stock alerts across all stores  
            - Update inventory after deliveries or sales

            **Delivery Management:**
            - Check scheduled deliveries and their status
            - Place new delivery orders for restocking
            - Update delivery statuses
            - Get recommendations for items that need restocking

            **Available Stores:**
            - Store 12: Downtown Store (123 Main St, Seattle, WA)
            - Store 34: Eastside Store (456 Oak Ave, Bellevue, WA)
            - Store 56: Northgate Store (789 Pine St, Seattle, WA)

            **Common Commands Examples:**
            - "Check inventory for store 12"
            - "Reorder 500 units of SKU 12345 for store 12"
            - "Show low stock alerts"
            - "Check deliveries for store 34" 
            - "What deliveries are scheduled?"
            - "Get delivery recommendations"
            - "Update delivery DEL-001 status to delivered"

            Always provide clear, actionable information. When stock is low, suggest appropriate reorder quantities.
            Use adaptive cards for complex data like inventory summaries, delivery schedules, and recommendations.

            Respond only in JSON format with the following JSON schema:
            
            {
                "contentType": "'Text' or 'AdaptiveCard' only",
                "content": "{The content of the response, may be plain text, or JSON based adaptive card for complex data}"
            }
            """

    def __init__(self, client: AzureChatCompletion):

        self.client = client

        execution_settings = OpenAIPromptExecutionSettings()
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        execution_settings.temperature = 0
        execution_settings.top_p = 1
        self.execution_settings = execution_settings

    async def invoke_agent(
        self, input: str, chat_history: ChatHistory
    ) -> dict[str, Any]:

        thread = ChatHistoryAgentThread()
        kernel = Kernel()

        chat_history.add_user_message(input)

        agent = ChatCompletionAgent(
            service=self.client,
            name=InventoryDeliveryAgent.agent_name,
            instructions=InventoryDeliveryAgent.agent_instructions,
            kernel=kernel,
            arguments=KernelArguments(
                settings=self.execution_settings,
            ),
        )

        agent.kernel.add_plugin(plugin=DateTimePlugin(), plugin_name="datetime")
        kernel.add_plugin(plugin=AdaptiveCardPlugin(), plugin_name="adaptiveCard")
        kernel.add_plugin(plugin=InventoryManagementPlugin(), plugin_name="inventory")
        kernel.add_plugin(plugin=DeliveryManagementPlugin(), plugin_name="delivery")

        resp: str = ""

        async for chat in agent.invoke(chat_history.to_prompt(), thread=thread):
            chat_history.add_message(chat.content)
            resp += chat.content.content

        # if resp has a json\n prefix, remove it
        if "json\n" in resp:
            resp = resp.replace("json\n", "")
            resp = resp.replace("```", "")

        resp = resp.strip()

        try:
            json_node: dict = json.loads(resp)
            result = InventoryDeliveryAgentResponse.model_validate(json_node)
            return result
        except Exception as e:
            return await self.invoke_agent(
                "That response did not match the expected format. Please try again. Error: "
                + str(e),
                chat_history,
            )
