#!/usr/bin/env python3
"""
MATRYOSHKA AUTO-REVIEW MCP Server

MCP-сервер для автоматического код-ревью Pull Request'ов.
Использует OpenRouter API (Nemotron 120B) для анализа кода.

Usage:
    python server.py
    
MCP Tools:
    - list_open_prs: Список открытых PR
    - get_pr_diff: Diff конкретного PR
    - analyze_pr: AI-анализ PR
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from github_client import GitHubClient
from ai_reviewer import AIReviewer
from file_filter import FileFilter

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto-review.log', encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger('matryoshka-auto-review')

# Сервер MCP
app = Server("matryoshka-auto-review")


class Config:
    """Конфигурация сервера."""
    
    def __init__(self):
        # GitHub
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv("GITHUB_REPO", "matryoshka/matryoshka-auto-review")
        
        # OpenRouter
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
        
        # Filter
        self.custom_ignore = json.loads(os.getenv("IGNORE_EXTENSIONS", "[]"))
        self.custom_review = json.loads(os.getenv("REVIEW_EXTENSIONS", "[]"))
        
        # Debug
        self.debug = os.getenv("AUTO_REVIEW_DEBUG", "0") == "1"
    
    def validate(self) -> List[str]:
        """Проверить конфигурацию."""
        errors = []
        
        if not self.github_token:
            errors.append("GITHUB_TOKEN not set")
        
        if not self.openrouter_key:
            errors.append("OPENROUTER_API_KEY not set")
        
        if '/' not in self.github_repo:
            errors.append(f"Invalid GITHUB_REPO format: {self.github_repo}")
        
        return errors
    
    def __repr__(self) -> str:
        return (
            f"Config(repo={self.github_repo}, "
            f"model={self.model}, debug={self.debug})"
        )


# Глобальная конфигурация
config = Config()
github_client: Optional[GitHubClient] = None
ai_reviewer: Optional[AIReviewer] = None
file_filter: Optional[FileFilter] = None


def init_clients():
    """Инициализировать клиенты."""
    global github_client, ai_reviewer, file_filter
    
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(f"Configuration error: {error}")
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    github_client = GitHubClient(config.github_token, config.github_repo)
    ai_reviewer = AIReviewer(
        api_key=config.openrouter_key,
        model=config.model
    )
    file_filter = FileFilter(
        custom_ignore=config.custom_ignore,
        custom_review=config.custom_review
    )
    
    logger.info(f"Initialized: {config}")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Список доступных MCP инструментов."""
    return [
        Tool(
            name="list_open_prs",
            description="Список открытых Pull Request'ов в репозитории",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "enum": ["open", "closed", "all"],
                        "default": "open",
                        "description": "Состояние PR"
                    },
                    "per_page": {
                        "type": "integer",
                        "default": 10,
                        "description": "Количество результатов (max 100)"
                    }
                }
            }
        ),
        Tool(
            name="get_pr_diff",
            description="Получить diff (изменения) конкретного Pull Request",
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_number": {
                        "type": "integer",
                        "description": "Номер Pull Request"
                    },
                    "filter_binary": {
                        "type": "boolean",
                        "default": True,
                        "description": "Фильтровать бинарные файлы"
                    }
                },
                "required": ["pr_number"]
            }
        ),
        Tool(
            name="analyze_pr",
            description="AI-анализ Pull Request с поиском проблем и уязвимостей",
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_number": {
                        "type": "integer",
                        "description": "Номер Pull Request"
                    },
                    "include_binary": {
                        "type": "boolean",
                        "default": False,
                        "description": "Включать бинарные файлы в анализ"
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["all", "security", "performance", "style"],
                        "default": "all",
                        "description": "Фокус анализа"
                    }
                },
                "required": ["pr_number"]
            }
        ),
        Tool(
            name="create_review_comment",
            description="Создать комментарий к Pull Request",
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_number": {
                        "type": "integer",
                        "description": "Номер Pull Request"
                    },
                    "body": {
                        "type": "string",
                        "description": "Текст комментария"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Путь к файлу (для inline комментария)"
                    },
                    "line_number": {
                        "type": "integer",
                        "description": "Номер строки (для inline комментария)"
                    }
                },
                "required": ["pr_number", "body"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Вызов MCP инструмента."""
    try:
        if name == "list_open_prs":
            return await handle_list_open_prs(arguments)
        elif name == "get_pr_diff":
            return await handle_get_pr_diff(arguments)
        elif name == "analyze_pr":
            return await handle_analyze_pr(arguments)
        elif name == "create_review_comment":
            return await handle_create_review_comment(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.exception(f"Error in {name}: {e}")
        return [TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


async def handle_list_open_prs(arguments: Dict[str, Any]) -> List[TextContent]:
    """Обработка list_open_prs."""
    state = arguments.get("state", "open")
    per_page = min(arguments.get("per_page", 10), 100)
    
    prs = github_client.list_open_prs(state=state, per_page=per_page)
    
    if not prs:
        return [TextContent(type="text", text="📭 Нет открытых PR")]
    
    result = ["📋 **Открытые Pull Request'ы:**\n"]
    
    for pr in prs:
        result.append(
            f"**#{pr['number']}: {pr['title']}**\n"
            f"- Автор: @{pr['user']['login']}\n"
            f"- Создан: {pr['created_at']}\n"
            f"- Статус: {pr['state']}\n"
            f"- URL: {pr['html_url']}\n"
        )
    
    return [TextContent(type="text", text="\n".join(result))]


async def handle_get_pr_diff(arguments: Dict[str, Any]) -> List[TextContent]:
    """Обработка get_pr_diff."""
    pr_number = arguments["pr_number"]
    filter_binary = arguments.get("filter_binary", True)
    
    # Получаем PR
    pr = github_client.get_pr(pr_number)
    
    # Получаем diff
    files = github_client.get_pr_diff(pr_number)
    
    # Фильтруем
    if filter_binary:
        filtered = file_filter.filter_diff(files)
        files = filtered['files']
        stats = f"\n📊 Отфильтровано: {filtered['skipped_files']} бинарных файлов\n"
    else:
        stats = ""
    
    result = [
        f"📝 **PR #{pr_number}: {pr['title']}**\n",
        f"👤 Автор: @{pr['user']['login']}",
        f"📁 Файлов: {len(files)}",
        stats,
        "\n" + "="*60 + "\n"
    ]
    
    for file in files:
        result.append(f"\n📁 {file['filename']} [{file['status']}]\n")
        if 'patch' in file:
            result.append(file['patch'])
        result.append("\n" + "-"*60)
    
    return [TextContent(type="text", text="\n".join(result))]


async def handle_analyze_pr(arguments: Dict[str, Any]) -> List[TextContent]:
    """Обработка analyze_pr."""
    pr_number = arguments["pr_number"]
    include_binary = arguments.get("include_binary", False)
    focus = arguments.get("focus", "all")
    
    logger.info(f"Analyzing PR #{pr_number}...")
    
    # Получаем PR
    pr = github_client.get_pr(pr_number)
    
    # Получаем diff
    files = github_client.get_pr_diff(pr_number)
    
    # Фильтруем
    if not include_binary:
        filtered = file_filter.filter_diff(files)
        files = filtered['files']
    
    if not files:
        return [TextContent(
            type="text",
            text="❌ Нет файлов для анализа (возможно, все бинарные)"
        )]
    
    # AI анализ
    logger.info(f"Sending {len(files)} files to AI...")
    review = ai_reviewer.analyze_diff(
        files=files,
        pr_title=pr['title'],
        pr_description=pr.get('body', '')
    )
    
    result = [
        f"🤖 **AI Review для PR #{pr_number}: {pr['title']}**\n",
        f"🧠 Модель: {ai_reviewer.model}",
        f"📁 Файлов: {len(files)}",
        "\n" + "="*60 + "\n",
        review
    ]
    
    return [TextContent(type="text", text="\n".join(result))]


async def handle_create_review_comment(arguments: Dict[str, Any]) -> List[TextContent]:
    """Обработка create_review_comment."""
    pr_number = arguments["pr_number"]
    body = arguments["body"]
    file_path = arguments.get("file_path")
    line_number = arguments.get("line_number")
    
    if file_path and line_number:
        comment = github_client.create_comment(
            pr_number=pr_number,
            body=body,
            path=file_path,
            position=line_number
        )
    else:
        comment = github_client.create_comment(
            pr_number=pr_number,
            body=body
        )
    
    return [TextContent(
        type="text",
        text=f"✅ Комментарий создан: {comment['html_url']}"
    )]


async def main():
    """Точка входа."""
    logger.info("Starting MATRYOSHKA Auto-Review MCP Server...")
    
    try:
        init_clients()
        logger.info("Clients initialized successfully")
    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
