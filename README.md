# FastAPI LangChain Chatbot

A modern web application that provides a chat interface for interacting with various Large Language Models (LLMs) through a unified interface. Built with FastAPI, LangChain, and featuring conversation management, MCP server integration, and automatic chart generation.

## Features

- 🤖 **Multi-provider LLM Support**: OpenAI, Grok, and Anthropic (Claude)
- 💬 **Conversation Management**: Save, load, and delete chat conversations
- 📊 **Automatic Chart Generation**: Detects chart requests and generates visualizations
- 🔌 **MCP Server Integration**: Add and manage Model Context Protocol servers
- 🌐 **Real-time Chat**: WebSocket support for streaming responses
- 🎨 **Modern UI**: Blue-themed minimalist design with responsive layout
- 🗄️ **SQLite Database**: Lightweight database with SQLAlchemy ORM

## Quick Start

### Prerequisites

- Python 3.12+
- uv package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fastapi-langchain-chatbot
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the application:
```bash
uv run main.py
```

5. Open your browser and navigate to:
- Main application: http://localhost:8000
- API documentation: http://localhost:8000/docs
- Configuration status: http://localhost:8000/api/config/status

## Configuration

### Environment Variables

The application uses environment variables for configuration. Copy `.env.example` to `.env` and customize:

```bash
# Application Settings
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./chatbot.db

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
GROK_API_KEY=your_grok_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Chart Settings
MAX_CHART_DATA_POINTS=1000
DEFAULT_CHART_TYPE=line

# WebSocket Settings
WEBSOCKET_TIMEOUT=300
```

### Environment-Specific Configuration

- **Development**: Use `.env.development` for development settings
- **Production**: Use `.env.production` for production deployment

### Configuration Management

The application includes a comprehensive configuration management system:

- **Configuration Manager**: Validates environment and manages settings
- **Provider Configs**: Individual configuration for each LLM provider
- **Runtime Validation**: Checks configuration health at startup
- **Configuration API**: RESTful endpoints for configuration management

## API Endpoints

### Chat Endpoints

- `POST /api/chat/send` - Send a message to the chat
- `GET /api/chat/conversations` - List all conversations
- `POST /api/chat/conversations` - Create new conversation
- `DELETE /api/chat/conversations/{id}` - Delete conversation
- `WS /ws/chat/{conversation_id}` - WebSocket for real-time chat

### MCP Server Endpoints

- `GET /api/mcp/servers` - List MCP servers
- `POST /api/mcp/servers` - Add MCP server
- `PUT /api/mcp/servers/{id}` - Update MCP server
- `DELETE /api/mcp/servers/{id}` - Remove MCP server

### Configuration Endpoints

- `GET /api/config/status` - Configuration health status
- `GET /api/config/summary` - Configuration summary
- `GET /api/config/providers` - Available LLM providers
- `GET /api/config/system-info` - System information

## Project Structure

```
app/
├── config/          # Configuration management
│   ├── database.py      # Database connection setup
│   ├── settings.py      # Pydantic settings
│   ├── config_manager.py # Enhanced configuration manager
│   └── utils.py         # Configuration utilities
├── models/          # SQLAlchemy data models
│   ├── conversation.py  # Conversation model
│   ├── message.py       # Message model
│   └── mcp_server.py    # MCP server model
├── providers/       # LLM provider implementations
│   ├── base.py          # Base provider class
│   ├── openai_provider.py # OpenAI integration
│   └── grok_provider.py   # Grok integration
├── services/        # Business logic services
│   ├── llm_manager.py     # LLM provider management
│   ├── chat_service.py    # Chat business logic
│   ├── chart_analyzer.py  # Chart generation
│   └── mcp_manager.py     # MCP server management
├── routers/         # FastAPI API endpoints
│   ├── chat.py          # Chat endpoints
│   ├── mcp.py           # MCP endpoints
│   ├── config.py        # Configuration endpoints
│   └── websocket.py     # WebSocket handler
├── schemas/         # Pydantic request/response models
│   ├── chat.py          # Chat schemas
│   └── mcp.py           # MCP schemas
├── static/          # Frontend assets
│   ├── css/style.css    # Blue-themed CSS
│   └── js/             # JavaScript files
├── templates/       # Jinja2 HTML templates
│   └── index.html       # Main chat interface
└── utils/          # Utility functions
```

## Development

### Setting Up Development Environment

1. Copy development configuration:
```bash
cp .env.development .env
```

2. Install development dependencies:
```bash
uv sync --dev
```

3. Run in development mode:
```bash
DEBUG=true uv run main.py
```

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Type checking
uv run mypy app/

# Code formatting
uv run black app/

# Linting
uv run flake8 app/
```

## Deployment

### Production Deployment

1. Set up production environment:
```bash
cp .env.production .env
# Edit with production values
```

2. Set environment:
```bash
export ENVIRONMENT=production
```

3. Run with production server:
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Configuration API Usage

### Check Configuration Status

```bash
curl http://localhost:8000/api/config/status
```

### Get Provider Information

```bash
curl http://localhost:8000/api/config/providers
```

### Validate Configuration

```bash
curl -X POST http://localhost:8000/api/config/validate \\
  -H "Content-Type: application/json" \\
  -d '{"keys": ["OPENAI_API_KEY", "DATABASE_URL"]}'
```

## Chart Generation

The application automatically detects chart requests in user messages and generates appropriate visualizations using Chart.js. Supported chart types:

- Line charts
- Bar charts  
- Pie charts
- Scatter plots
- Area charts

Example usage:
```
User: "создай график продаж по месяцам"
Assistant: [Generates response with chart data]
```

## MCP Server Integration

Model Context Protocol (MCP) servers can be added to extend the chatbot's capabilities:

1. Add server via API or web interface
2. Configure server endpoint and settings
3. Server capabilities are automatically integrated into chat

## WebSocket Real-time Chat

The application supports real-time chat via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/conversation-id');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle streaming response
};
```

## Troubleshooting

### Common Issues

1. **No LLM providers available**: Check API keys in `.env` file
2. **Database connection failed**: Ensure SQLite file permissions
3. **WebSocket connection issues**: Check firewall and CORS settings
4. **Chart generation not working**: Verify Chart.js library loading

### Configuration Validation

Use the configuration API to diagnose issues:

```bash
# Check overall health
curl http://localhost:8000/api/config/status

# Get system information
curl http://localhost:8000/api/config/system-info
```

### Logs

Application logs are stored in the `logs/` directory:
- `application.log` - Error logs
- Console output - Info and debug logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure quality checks pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the configuration API endpoints
- Review the logs in the `logs/` directory
- Create an issue in the repository