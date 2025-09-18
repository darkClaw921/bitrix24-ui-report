# Архитектура проекта FastAPI LangChain Chatbot

## Обзор проекта

Современный чат с битрикс24 с поддержкой множественных LLM провайдеров, управлением диалогами, интеграцией MCP серверов и автоматическим созданием графиков.

## Структура проекта

### Корневая директория
- `main.py` - точка входа приложения FastAPI
- `pyproject.toml` - конфигурация проекта и зависимости
- `start.sh` - скрипт запуска
- `README.md` - документация проекта

### Конфигурация (`app/config/`)
- `settings.py` - настройки приложения
- `database.py` - конфигурация базы данных SQLite
- `config_manager.py` - менеджер конфигурации
- `utils.py` - утилиты конфигурации

### Модели данных (`app/models/`)
- `conversation.py` - модель диалогов
- `message.py` - модель сообщений
- `mcp_server.py` - модель MCP серверов
- `provider_config.py` - модель конфигураций провайдеров

### Провайдеры LLM (`app/providers/`)
- `base.py` - базовый класс провайдера
- `openai_provider.py` - провайдер OpenAI
- `grok_provider.py` - провайдер Grok

### API роутеры (`app/routers/`)
- `chat.py` - эндпоинты для чата
- `conversations.py` - эндпоинты управления диалогами
- `config.py` - эндпоинты конфигурации
- `mcp.py` - эндпоинты MCP серверов
- `providers.py` - эндпоинты конфигурации провайдеров
- `websocket.py` - WebSocket соединения

#### Эндпоинты MCP (`/api/mcp`)
- `GET /servers` — список MCP серверов
- `POST /servers` — создание сервера (`name`, `url`, `transport`, `env`, ...)
- `GET /servers/{id}` — получить сервер
- `PUT /servers/{id}` — обновить сервер
- `DELETE /servers/{id}` — удалить сервер
- `POST /test-connection` — тест соединения (`url` или `endpoint`)
- `POST /servers/{server_id}/execute` — выполнить запрос к серверу
- `GET /tools` — получить список tools со всех активных MCP серверов
- `GET /prompts/{server_name}/{prompt_name}` — получить prompt с указанного MCP сервера

### Схемы Pydantic (`app/schemas/`)
- `chat.py` - схемы для чата
- `mcp.py` - схемы для MCP

### Сервисы (`app/services/`)
- `chat_service.py` - логика чата
- `llm_manager.py` - управление LLM провайдерами
- `mcp_manager.py` - управление MCP серверами
- `chart_analyzer.py` - анализ и создание графиков
- `mcp_client.py` - клиент для работы с активными MCP серверами через `MultiServerMCPClient`

### Статические файлы (`app/static/`)

#### CSS (`app/static/css/`)
- `style.css` - основные стили приложения в синей минималистичной тематике

#### JavaScript (`app/static/js/`)
- `chat.js` - логика чат-интерфейса
- `websocket.js` - WebSocket соединения
- `charts.js` - функции для работы с графиками

#### Изображения (`app/static/images/`)
- Директория для статических изображений

### Шаблоны (`app/templates/`)
- `index.html` - главная страница чат-интерфейса
- `conversations.html` - страница управления диалогами
- `settings.html` - страница настроек провайдеров и MCP серверов

## Технологии

### Backend
- **FastAPI** - веб-фреймворк
- **SQLAlchemy** - ORM
- **SQLite** - база данных
- **LangChain** - интеграция с LLM
- **Pydantic** - валидация данных
- **WebSockets** - реальное время связь

### Frontend
- **HTML5/CSS3** - разметка и стили
- **JavaScript (ES6+)** - клиентская логика
- **Chart.js** - визуализация данных
- **Lucide Icons** - иконки
- **Google Fonts (Inter)** - типографика

### Управление зависимостями
- **uv** - менеджер пакетов Python

## Конфигурация статических файлов

Статические файлы размещены в `app/static/` и доступны через URL `/static/`:
- CSS файлы: `/static/css/style.css`
- JavaScript файлы: `/static/js/[filename].js`
- Изображения: `/static/images/[filename]`

В `main.py` статические файлы монтируются через:
```python
app.mount("/static", StaticFiles(directory="app/static"), name="static")
```

В HTML шаблонах используется Jinja2 функция `url_for()`:
```html
<link rel="stylesheet" href="{{ url_for('static', path='/css/style.css') }}">
<script src="{{ url_for('static', path='/js/chat.js') }}"></script>
```

## База данных

Используется SQLite с четырьмя основными таблицами:
- `conversations` - диалоги пользователей
- `messages` - сообщения в диалогах
- `mcp_servers` - конфигурация MCP серверов
- `provider_configs` - конфигурации LLM провайдеров

## Поддерживаемые LLM провайдеры

- **OpenAI** - GPT модели
- **Grok** - xAI модели
- **Anthropic** - Claude модели (планируется)

## Особенности архитектуры

1. **Модульность** - четкое разделение на слои (модели, сервисы, роутеры)
2. **Расширяемость** - легко добавлять новые LLM провайдеры
3. **Типизация** - полная поддержка типов через Pydantic
4. **Асинхронность** - все операции выполняются асинхронно
5. **WebSocket** - поддержка реального времени
6. **Автоматическая документация** - через FastAPI/OpenAPI