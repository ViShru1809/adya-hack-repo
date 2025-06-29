# Adya MCP Hackathon Integration Platform 🚀



A comprehensive integration platform for connecting multiple MCP (Model Context Protocol) servers with unified client interfaces.

## 🌟 Key Features

- **Multi-Server Integration**: Pre-configured connections to various MCP servers
- **Unified Client Interface**: Single entry point for all server communications
- **LLM Support**: Azure OpenAI, Gemini, and standard OpenAI integrations
- **Development Ready**: Quick-start virtual environment setup

# Available Tools

## Blender Tools

| Function Name                          | Description |
|----------------------------------------|-------------|
| `get_scene_info`                       | Get information about the current scene |
| `get_object_info`                      | Get information about a specific object |
| `get_viewport_screenshot`              | Capture a screenshot of the viewport |
| `execute_blender_code`                 | Execute Python code within Blender |
| `get_polyhaven_categories`             | Get asset categories from Poly Haven |
| `search_polyhaven_assets`              | Search for assets on Poly Haven |
| `download_polyhaven_asset`             | Download an asset from Poly Haven |
| `set_texture`                          | Apply a texture to an object |
| `get_polyhaven_status`                 | Check Poly Haven service status |
| `get_hyper3d_status`                  | Check Hyper3D service status |
| `get_sketchfab_status`                | Check Sketchfab service status |
| `search_sketchfab_models`             | Search for models on Sketchfab |
| `download_sketchfab_model`            | Download a model from Sketchfab |
| `generate_hyper3d_model_via_text`     | Generate 3D model using text input |
| `generate_hyper3d_model_via_images`  | Generate 3D model using image input |
| `poll_rodin_job_status`               | Check status of a Rodin job |
| `import_generated_asset`              | Import a generated asset into the scene |

## CoinStats Tools

| Function Name                     | Description |
|-----------------------------------|-------------|
| `get-coins`                       | Get list of coins |
| `get-coin-by-id`                  | Get coin details by ID |
| `get-coin-chart-by-id`            | Get chart data for a coin |
| `get-coin-avg-price`              | Get average price of a coin |
| `get-coin-exchange-price`         | Get exchange price for a coin |
| `get-ticker-exchanges`            | Get exchanges for a ticker |
| `get-ticker-markets`              | Get markets for a ticker |
| `get-blockchains`                 | Get blockchain information |
| `get-wallet-balance`              | Get wallet balance |
| `get-wallet-balances`             | Get multiple wallet balances |
| `get-wallet-sync-status`          | Check wallet sync status |
| `get-wallet-transactions`         | Get wallet transactions |
| `transactions-sync`               | Sync transactions |
| `get-exchanges`                   | Get exchange information |
| `get-exchange-balance`            | Get exchange balance |
| `get-exchange-sync-status`        | Check exchange sync status |
| `get-exchange-transactions`       | Get exchange transactions |
| `get-fiat-currencies`             | Get fiat currencies |
| `get-news-sources`                | Get news sources |
| `get-news`                       | Get news articles |
| `get-news-by-type`               | Get news by type |
| `get-news-by-id`                 | Get news by ID |
| `get-market-cap`                 | Get market capitalization |
| `get-portfolio-coins`            | Get portfolio coins |
| `get-portfolio-chart`            | Get portfolio chart |
| `get-portfolio-transactions`     | Get portfolio transactions |
| `add-portfolio-transaction`      | Add portfolio transaction |
| `get-currencies`                 | Get currency information |
| `save-share-token`               | Save share token |
| `get-share-token`                | Get share token |

## Readwise.io Tools

| Function Name               | Description |
|-----------------------------|-------------|
| `search_readwise_highlights` | Search through your Readwise highlights |

## Mermaid Tools

| Function Name               | Description |
|-----------------------------|-------------|
| `generate_mermaid_diagram`   | Generate a diagram using Mermaid syntax |

# 🛠️ Setup Instructions

### 1. Clone and Prepare
```bash
git clone https://github.com/ViShru1809/adya_mcp_hackathon.git
cd adya_mcp_hackathon
```

### 2. Python Client Setup

```bash
cd mcp_servers/python/clients
```

#### Create and activate virtual environment (Windows)

```bash
python -m venv venv
.\venv\Scripts\activate
```

#### Install dependencies

```bash
pip install -r requirements.txt
```
### 3. Run the Integration Server

```bash
python run.py
```

# EXPECTED OUTPUT:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                📈🚀✨ ADYA  📈🚀✨                        ║
║                  MCP Server Integration Hackathon 2k25 !!                    ║
║                                                                              ║
║  ✅ Server running on http://0.0.0.0:5001 ✅                                ║
║  ✅ MCP servers initialization started                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
```


# 🔌 Integrated MCP Servers

# MCP Servers Status

| Server Name | Location Path | Status |
|-------------|---------------|--------|
| Blender MCP | python/servers/blender-mcp | ✅ Live |
| CoinStats MCP | python/servers/coinstats-mcp | ✅ Live |
| MCP Mermaid | python/servers/mcp-mermaid | ✅ Live |
| Readwise MCP | python/servers/readwise-mcp | ✅ Live |

## If Incase of Missing Dependencies:
Run the following command:

```bash
pip install --upgrade -r requirements.txt
```


## Credentials :

### Gemini

Gemini API key : `AIzaSyB3-j9gYSLIYf8sParyBcq7SV7RFwSmx90`

Chat Model: `gemini-1.5-flash`

### Coinstats

COINSTATS API KEY: `"FNdJng7R6gp7l2I4gJa/RX3LjfszShG1fvP9BmcLgWs="`

### Readwise

ACCESS_TOKEN : `"wSuAgpIPD1lA5Bu0rDgO7VytpDFD6XXYRzLOabn1CSfmtW1Owq"`

# Working video:



https://github.com/user-attachments/assets/c701333b-a251-4cec-8f84-26d0afb2d14b



https://github.com/user-attachments/assets/1fc7ae7b-660c-4d70-a691-0c6a18636b0b



https://github.com/user-attachments/assets/115ab47d-e63e-4a9f-8bca-b494f736681c

