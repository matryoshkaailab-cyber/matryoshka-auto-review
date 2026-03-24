"""
AI Reviewer Module for MATRYOSHKA Auto-Review

Analyzes code changes using OpenRouter API (Nemotron 120B).
"""

import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI


class AIReviewer:
    """
    AI-ревьюер для анализа кода.
    
    Использует OpenRouter API с моделью Nemotron 120B.
    
    Проверяет:
    - Ошибки кода (bugs, anti-patterns)
    - Уязвимости безопасности (SQL injection, XSS)
    - Стиль кода (PEP8, naming conventions)
    - Производительность (оптимизации)
    - Документацию (комментарии, docstrings)
    """
    
    # Модель по умолчанию (бесплатная, 120B MoE)
    DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
    
    # Системный промпт
    SYSTEM_PROMPT = """
Ты — опытный Senior Software Engineer в команде MATRYOSHKA OS.
Твоя задача: проводить код-ревью Pull Request'ов.

ПРИНЦИПЫ РЕВЬЮ:
1. Будь конструктивным — предлагай решения, а не только критику
2. Будь кратким — без воды, только по делу
3. Будь точным — указывай конкретные строки и проблемы
4. Будь дружелюбным — используй эмодзи ✅⚠️❌

ЧТО ПРОВЕРЯТЬ:
🔴 CRITICAL (❌):
- Уязвимости безопасности (SQL injection, XSS, hardcoded secrets)
- Критические баги (null pointer, race conditions)
- Потеря данных

🟡 WARNING (⚠️):
- Отсутствие обработки ошибок
- Потенциальные проблемы производительности
- Сложный код (high cyclomatic complexity)

🟢 SUGGESTION (💡):
- Улучшения стиля кода
- Рефакторинг для читаемости
- Добавление документации

ФОРМАТ ОТВЕТА:
Для каждого файла:
```
📁 filename.py

❌ CRITICAL:
- Строка X: [описание проблемы]
  Решение: [как исправить]

⚠️ WARNING:
- Строка Y: [описание проблемы]
  Решение: [как исправить]

💡 SUGGESTION:
- [предложение по улучшению]
```

В конце — общее резюме:
```
📊 ИТОГО:
- Файлов: N
- Critical: X
- Warning: Y
- Suggestion: Z

✅ LGTM / ❌ NEEDS WORK
```
"""
    
    def __init__(self, api_key: Optional[str] = None, 
                 model: Optional[str] = None,
                 base_url: str = "https://openrouter.ai/api/v1"):
        """
        Инициализация AI-ревьюера.
        
        Args:
            api_key: OpenRouter API key (sk-or-v1-...)
            model: Модель для анализа (по умолчанию Nemotron 120B)
            base_url: OpenRouter API URL
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not provided")
        
        self.model = model or self.DEFAULT_MODEL
        self.base_url = base_url
        
        # OpenAI клиент (OpenRouter совместим с API OpenAI)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url
        )
    
    def analyze_diff(self, files: List[Dict[str, Any]], 
                     pr_title: str = "", 
                     pr_description: str = "") -> str:
        """
        Проанализировать diff PR.
        
        Args:
            files: Список файлов с изменениями из GitHub API
            pr_title: Заголовок PR
            pr_description: Описание PR
            
        Returns:
            Текст ревью
        """
        # Формируем промпт с diff
        diff_content = self._format_diff_for_prompt(files)
        
        user_prompt = f"""
PR Title: {pr_title}
PR Description: {pr_description}

CODE CHANGES:
{diff_content}

Проведи код-ревью согласно инструкциям.
"""
        
        # Запрос к OpenRouter
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.3,  # Низкая температура для точности
        )
        
        return response.choices[0].message.content
    
    def analyze_file(self, file_content: str, file_path: str, 
                     changes: Optional[List[Dict]] = None) -> str:
        """
        Проанализировать отдельный файл.
        
        Args:
            file_content: Содержимое файла
            file_path: Путь к файлу
            changes: Список изменений (diff hunk)
            
        Returns:
            Текст ревью
        """
        changes_str = ""
        if changes:
            changes_str = "\nCHANGES:\n" + json.dumps(changes, indent=2)
        
        user_prompt = f"""
File: {file_path}
{changes_str}

CONTENT:
{file_content}

Проведи код-ревью файла.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.3,
        )
        
        return response.choices[0].message.content
    
    def _format_diff_for_prompt(self, files: List[Dict[str, Any]]) -> str:
        """
        Отформатировать diff для промпта.
        
        Args:
            files: Файлы из GitHub API
            
        Returns:
            Отформатированный diff
        """
        result = []
        
        for file in files:
            filename = file.get('filename', 'unknown')
            status = file.get('status', 'modified')  # added, modified, removed
            patch = file.get('patch', '')
            
            result.append(f"\n{'='*60}")
            result.append(f"📁 {filename} [{status.upper()}]")
            result.append(f"{'='*60}")
            
            if patch:
                result.append(patch)
            else:
                result.append("(No diff available)")
        
        return "\n".join(result)
    
    def create_inline_comments(self, review_text: str, 
                               files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Создать inline комментарии из текста ревью.
        
        Парсит ревью и создаёт комментарии для конкретных строк.
        
        Args:
            review_text: Текст ревью от AI
            files: Файлы из GitHub API
            
        Returns:
            Список комментариев для GitHub API
        """
        comments = []
        
        # Простой парсинг (можно улучшить с regex)
        lines = review_text.split('\n')
        current_file = None
        current_line = None
        current_comment = []
        
        for line in lines:
            # Определяем файл
            if line.startswith('📁'):
                current_file = line.replace('📁', '').strip().split()[0]
            
            # Определяем строку (например, "Строка 42:")
            if 'Строка' in line and ':' in line:
                try:
                    line_num = int(''.join(filter(str.isdigit, line)))
                    current_line = line_num
                except ValueError:
                    pass
            
            # Собираем комментарий
            if current_file and current_line:
                current_comment.append(line)
        
        # TODO: Улучшить парсинг для production
        return comments
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Получить информацию о модели.
        
        Returns:
            Информация о модели
        """
        return {
            'model': self.model,
            'base_url': self.base_url,
            'provider': 'OpenRouter'
        }
