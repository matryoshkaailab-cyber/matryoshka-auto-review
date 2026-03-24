#!/usr/bin/env python3
"""
MATRYOSHKA AUTO-REVIEW - GitHub Actions Script

Автоматическое ревью PR через GitHub Actions.
Используется в workflow auto-review.yml
"""

import os
import sys
import json
from github_client import GitHubClient
from ai_reviewer import AIReviewer
from file_filter import FileFilter


def main():
    """Основная логика."""
    print("🤖 MATRYOSHKA Auto-Review starting...")
    
    # Получаем переменные окружения
    github_token = os.getenv("GITHUB_TOKEN")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
    
    # GitHub context (автоматически в Actions)
    event_path = os.getenv("GITHUB_EVENT_PATH")
    with open(event_path) as f:
        event = json.load(f)
    
    pr = event.get("pull_request", {})
    if not pr:
        print("❌ Not a PR event")
        sys.exit(0)
    
    pr_number = pr["number"]
    repo_name = os.getenv("GITHUB_REPOSITORY")
    
    print(f"📝 Analyzing PR #{pr_number} in {repo_name}")
    
    # Инициализация
    gh_client = GitHubClient(github_token, repo_name)
    ai_reviewer = AIReviewer(api_key=openrouter_key, model=model)
    file_filter = FileFilter()
    
    # Получаем diff
    print("📥 Fetching PR diff...")
    files = gh_client.get_pr_diff(pr_number)
    print(f"📁 Found {len(files)} files")
    
    # Фильтруем
    filtered = file_filter.filter_diff(files)
    files = filtered["files"]
    print(f"✅ After filter: {len(files)} files for review ({filtered['skipped_files']} skipped)")
    
    if not files:
        print("⚠️ No files to review (all binary)")
        with open("review-output.md", "w") as f:
            f.write("⚠️ Нет файлов для анализа (все файлы бинарные)")
        sys.exit(0)
    
    # AI анализ
    print("🧠 Running AI analysis...")
    pr_info = gh_client.get_pr(pr_number)
    review = ai_reviewer.analyze_diff(
        files=files,
        pr_title=pr_info.get("title", ""),
        pr_description=pr_info.get("body", "")
    )
    
    # Сохраняем результат
    with open("review-output.md", "w", encoding="utf-8") as f:
        f.write(review)
    
    print("✅ Review saved to review-output.md")
    
    # Определяем есть ли критичные проблемы
    has_issues = "❌" in review or "⚠️" in review
    
    # Выводим для GitHub Actions
    with open(os.getenv("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write(f"has_issues={str(has_issues).lower()}\n")
    
    if has_issues:
        print("⚠️ Issues found, posting review...")
    else:
        print("✅ No issues, LGTM!")
    
    print("🤖 MATRYOSHKA Auto-Review complete!")


if __name__ == "__main__":
    main()
