# AI Foundry Inventory & Delivery Management Agent

This project demonstrates how to develop AI agents locally using Azure AI Foundry through Semantic Kernel and the Microsoft 365 Agents Framework, specifically showcasing an **Inventory and Delivery Management Agent** for retail operations.

This Agent Sample provides a comprehensive business use case for integrating Semantic Kernel with the Microsoft 365 Agents SDK to build powerful AI agents that can manage inventory, track deliveries, and assist with retail operations through M365 Copilot. It serves as both a learning tool and a practical foundation for developing custom business agents that integrate seamlessly with the Microsoft 365 ecosystem.

***Note:*** This sample requires JSON output from the model which works best from newer versions of the model such as `gpt-4o-mini`.

## Agent Features

This **Inventory & Delivery Management Agent** provides comprehensive retail operations support:

### 🏪 **Inventory Management**
- **Stock Level Monitoring**: Check current inventory across all stores and SKUs
- **Low Stock Alerts**: Automated alerts for items below minimum thresholds
- **Inventory Updates**: Track stock changes after deliveries and sales
- **Multi-Store Support**: Manage inventory for multiple retail locations

### 🚚 **Delivery Management**
- **Delivery Tracking**: Monitor scheduled deliveries and their status
- **Order Placement**: Place new delivery orders with automatic calculations
- **Status Updates**: Update delivery statuses throughout the fulfillment process
- **Smart Recommendations**: AI-powered suggestions for restocking needs

### 📋 **Sample Commands**
The agent responds to natural language commands such as:
- `"Check inventory for store 12"`
- `"Reorder 500 units of SKU 12345 for store 12"`
- `"Show low stock alerts"`
- `"Check deliveries for store 34"`
- `"What deliveries are scheduled?"`
- `"Get delivery recommendations"`
- `"Update delivery DEL-001 status to delivered"`

### 🏬 **Available Stores**
- **Store 12**: Downtown Store (123 Main St, Seattle, WA)
- **Store 34**: Eastside Store (456 Oak Ave, Bellevue, WA)
- **Store 56**: Northgate Store (789 Pine St, Seattle, WA)

### 📱 **Rich User Experience**
The agent provides responses through:
- **Adaptive Cards**: Beautiful, interactive cards for complex data
- **Natural Language**: Clear, actionable text responses
- **Action Buttons**: Interactive elements like "Track Delivery" buttons

## Prerequisites

-  [Python](https://www.python.org/) version 3.9 or higher
-  [dev tunnel](https://learn.microsoft.com/azure/developer/dev-tunnels/get-started?tabs=windows) (for local development)
- You will need an Azure OpenAI, with the preferred model of `gpt-4o-mini`.

## Local Setup

### Configure Azure Bot Service

1. [Create an Azure Bot using client secret](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/azure-bot-create-single-secret)
   - Record the Application ID, the Tenant ID, and the Client Secret for use below

1. Configuring the token connection in the Agent settings
    1. Open the `env.TEMPLATE` file in the root of the sample project, rename it to `.env` and configure the following values:
      1. Set the **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID** to the AppId of the bot identity.
      2. Set the **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET** to the Secret that was created for your identity. *This is the `Secret Value` shown in the AppRegistration*.
      3. Set the **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID** to the Tenant Id where your application is registered.

1. Configure the Azure OpenAI settings in the Agent settings
   1. Set **AZURE_OPENAI_API_VERSION** to an OpenAI API version such as ` 2025-01-01-preview`
   1. Set **AZURE_OPENAI_ENDPOINT** to the endpoint for your Azure OpenAI instance. For example, if using an Azure AI Foundry named `testing`, the endpoint would be `https://endpoint.openai.azure.com/`
   1. Set **AZURE_OPENAI_API_KEY** to the key.


1. Run `dev tunnels`. See [Create and host a dev tunnel](https://learn.microsoft.com/azure/developer/dev-tunnels/get-started?tabs=windows) and host the tunnel with anonymous user access command as shown below:

   ```bash
   devtunnel host -p 3978 --allow-anonymous
   ```

1. Take note of the url shown after `Connect via browser:`

1. On the Azure Bot, select **Settings**, then **Configuration**, and update the **Messaging endpoint** to `{tunnel-url}/api/messages`

### Running the Agent

1. Open this folder from your IDE or Terminal of preference
1. (Optional but recommended) Set up virtual environment and activate it.
1. Install dependencies

```sh
pip install -r requirements.txt
```

### Run in localhost, anonymous mode

1. Start the application

```sh
python -m src.main
```

At this point you should see the message 

```text
======== Running on http://localhost:3978 ========
```

The agent is ready to accept messages.

## Accessing the Agent

### Testing Locally with Teams App Test Tool

Before testing in Azure Bot Service Web Chat, it's recommended to test your agent locally using the Microsoft 365 Agents Playground.

1. **Install the Teams App Test Tool**
   
   Open a separate terminal and install the tool:
   ```powershell
   winget install agentsplayground
   ```

2. **Configure for Local Testing**
   
   In your `.env` file, ensure development mode is enabled:
   ```
   DEVELOPMENT_MODE=true
   ```

3. **Start the Test Tool**
   
   In the separate terminal, run:
   ```powershell
   teamsapptester
   ```
   
   This will:
   - Launch a local testing environment
   - Open your browser to the Microsoft 365 Agents Playground
   - Connect to your running agent on `http://localhost:3978`

4. **Test Your Agent**
   
   Use the playground interface to send inventory and delivery management commands to your agent:
   - Try: `"Check inventory for store 12"`
   - Try: `"Reorder 100 units of SKU 12345 for store 12"`
   - Try: `"Show delivery recommendations"`
   
   Verify the agent responds with appropriate inventory data and adaptive cards before proceeding to other testing methods.

### Using the Agent in WebChat

1. Go to your Azure Bot Service resource in the Azure Portal and select **Test in WebChat**

## Upload the Agent to Microsoft Teams and M365 Copilot

To make your agent available in Microsoft Teams and Microsoft 365 Copilot, you need to create and upload a Teams app manifest. This process packages your bot as a Teams application that can be installed and used across the Microsoft 365 ecosystem.

### Prerequisites for Teams Deployment

- Your Azure Bot Service must have the **Microsoft Teams channel** enabled under **Channels**
- You need **Global Administrator** or **Teams Administrator** permissions to upload custom apps
- Custom app uploads must be enabled in your organization's Teams settings

### Create the Teams App Manifest

1. **Prepare the manifest files**
   - Use the files in the `appManifest` folder of this project
   - Ensure you have the required icon files:
     - `color.png` (192x192 pixels)
     - `outline.png` (32x32 pixels, transparent background)

2. **Configure the manifest.json**
   - Replace `<<AAD_APP_CLIENT_ID>>` with your Azure Bot's **Application ID**
   - Replace `<<BOT_DOMAIN>>` with your dev tunnel domain (e.g., `abc123-3978.inc1.devtunnels.ms`)
   - Update the `validDomains` array with your bot's domain
   - Ensure the `botId` matches your Azure Bot's Application ID
   - The manifest is already configured for the **Inventory & Delivery Management Agent**

3. **Create the deployment package**
   ```powershell
   # Navigate to the appManifest folder
   cd appManifest
   
   # Create a ZIP file with the manifest and icons
   Compress-Archive -Path manifest.json,color.png,outline.png -DestinationPath "../agent-manifest.zip" -Force
   ```

### Deploy to Microsoft 365

1. **Enable Teams Channel**
   - Go to your Azure Bot Service in the Azure Portal
   - Under **Settings** → **Channels**, add the **Microsoft Teams** channel if not already present

2. **Upload to Microsoft 365**
   - Navigate to the **Microsoft 365 Admin Center**
   - Go to **Settings** → **Integrated apps**
   - Click **Upload custom apps**
   - Select your `agent-manifest.zip` file
   - Follow the approval and deployment process

3. **Alternative Upload Methods**
   - **Teams Admin Center**: Go to **Teams apps** → **Manage apps** → **Upload**
   - **Teams Client**: Go to **Apps** → **Upload a custom app** (for personal testing)

### Verify Deployment

After successful upload:
- The **Inventory & Delivery Management Agent** will appear in **Microsoft Teams** under Apps
- It will be available in **Microsoft 365 Copilot** as a custom business agent
- Users can install and interact with the agent for retail operations through chat
- Test with commands like `"Check inventory for store 12"` to verify functionality

### Important Notes

- **Development Mode**: Set `DEVELOPMENT_MODE=false` in your `.env` file for production deployment
- **Authentication**: Ensure your bot's messaging endpoint is correctly configured with your dev tunnel URL
- **Testing**: Test in Azure Bot Service Web Chat first before deploying to Teams
- **Permissions**: The agent respects your organization's app permission policies

## Further reading
To learn more about building Agents, see our [Microsoft 365 Agents SDK](https://github.com/microsoft/agents) repo.

For more information on logging configuration, see the logging section in the Quickstart Agent sample README.