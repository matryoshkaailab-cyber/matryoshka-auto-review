# 🤖 MATRYOSHKA AUTO-REVIEW

**AI-powered automated code review for MATRYOSHKA OS**

Использует **OpenRouter API** (Nemotron 120B Free) для автоматического анализа Pull Request'ов.

---

## 📋 ВОЗМОЖНОСТИ

| Функция | Описание |
|---------|----------|
| **list_open_prs** | Список открытых PR в репозитории |
| **get_pr_diff** | Diff конкретного PR с фильтрацией бинарных файлов |
| **analyze_pr** | AI-анализ кода (баги, уязвимости, стиль) |
| **create_review_comment** | Создание комментариев к PR |

---

## 🏗️ АРХИТЕКТУРА

```
Claude Desktop ──MCP──▶ server.py ──GitHub API──▶ PR Diff
                              │
                         File Filter
                              │
                         OpenRouter API
                              │
                      Nemotron 120B Free
                              │
                         AI Review
```

---

## 🚀 УСТАНОВКА

### 1. Клонирование

```bash
git clone https://github.com/matryoshka/matryoshka-auto-review.git
cd matryoshka-auto-review
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте `.env` файл:

```bash
# GitHub
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=matryoshka/matryoshka-auto-review

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-your_key_here
OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free

# Debug (опционально)
AUTO_REVIEW_DEBUG=0
```

---

## 🔧 НАСТРОЙКА CLAUDE DESKTOP

### Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "matryoshka-auto-review": {
      "command": "python",
      "args": ["C:\\path\\to\\matryoshka-auto-review\\server.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here",
        "GITHUB_REPO": "matryoshka/matryoshka-auto-review",
        "OPENROUTER_API_KEY": "sk-or-v1-your_key_here",
        "OPENROUTER_MODEL": "nvidia/nemotron-3-super-120b-a12b:free"
      }
    }
  }
}
```

### macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "matryoshka-auto-review": {
      "command": "python",
      "args": ["/path/to/matryoshka-auto-review/server.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here",
        "GITHUB_REPO": "matryoshka/matryoshka-auto-review",
        "OPENROUTER_API_KEY": "sk-or-v1-your_key_here"
      }
    }
  }
}
```

**После настройки перезапустите Claude Desktop!**

---

## 📖 ИСПОЛЬЗОВАНИЕ

### Примеры промптов в Claude Desktop:

**Показать открытые PR:**
```
Покажи открытые Pull Request'ы
```

**Получить diff PR:**
```
Покажи изменения в PR #42
```

**AI-анализ PR:**
```
Проанализируй PR #42, найди проблемы безопасности
```

**Создать комментарий:**
```
Добавь комментарий к PR #15: "LGTM, отличный код!"
```

---

## 🎯 MCP ИНСТРУМЕНТЫ

### 1. `list_open_prs`

**Описание:** Список открытых PR

**Параметры:**
- `state` (string): "open", "closed", "all" (default: "open")
- `per_page` (integer): Количество результатов (max: 100)

**Пример:**
```
list_open_prs(state="open", per_page=10)
```

---

### 2. `get_pr_diff`

**Описание:** Diff конкретного PR

**Параметры:**
- `pr_number` (integer): Номер PR **[required]**
- `filter_binary` (boolean): Фильтровать бинарные файлы (default: true)

**Пример:**
```
get_pr_diff(pr_number=42, filter_binary=true)
```

---

### 3. `analyze_pr`

**Описание:** AI-анализ PR

**Параметры:**
- `pr_number` (integer): Номер PR **[required]**
- `include_binary` (boolean): Включать бинарные файлы (default: false)
- `focus` (string): "all", "security", "performance", "style" (default: "all")

**Пример:**
```
analyze_pr(pr_number=42, focus="security")
```

---

### 4. `create_review_comment`

**Описание:** Создание комментария

**Параметры:**
- `pr_number` (integer): Номер PR **[required]**
- `body` (string): Текст комментария **[required]**
- `file_path` (string): Путь к файлу (для inline)
- `line_number` (integer): Номер строки (для inline)

**Пример:**
```
create_review_comment(
    pr_number=42,
    body="❌ Строка 23: SQL Injection уязвимость!",
    file_path="src/database.py",
    line_number=23
)
```

---

## 🔐 АУТЕНТИФИКАЦИЯ

### GitHub Token

1. Перейдите на [github.com/settings/tokens](https://github.com/settings/tokens)
2. Создайте новый токен (Classic)
3. Выберите скоупы:
   - ✅ `repo` (Full control of private repositories)
4. Скопируйте токен (начинается с `ghp_`)

### OpenRouter API Key

1. Перейдите на [openrouter.ai/keys](https://openrouter.ai/keys)
2. Создайте новый ключ
3. Скопируйте ключ (начинается с `sk-or-v1-`)

---

## 📊 ФИЛЬТРАЦИЯ ФАЙЛОВ

### Ревьювятся (код):
```
.py, .js, .ts, .jsx, .tsx, .vue, .svelte
.html, .css, .scss, .sass, .less
.cs, .java, .kt, .scala, .go, .rs, .php
.rb, .swift, .m, .mm
.json, .xml, .yaml, .yml, .toml, .ini
.md, .txt, .rst, .adoc
.sh, .bash, .zsh, .fish, .ps1, .bat
.sql, .graphql
.tf, .hcl, .dockerfile
```

### Игнорируются (бинарные):
```
.dll, .so, .exe, .bin, .dat, .db
.png, .jpg, .jpeg, .gif, .bmp, .svg
.mp3, .wav, .ogg, .mp4, .avi
.meta, .prefab, .unity, .asset, .mat
.pyc, .pyo, .class, .o
.zip, .tar, .gz, .rar
.gitignore, .DS_Store, .env
```

---

## 🛠️ ДИАГНОСТИКА

### Проверка соединения

```bash
python -c "from github_client import GitHubClient; c = GitHubClient('token', 'owner/repo'); print(c.test_connection())"
```

### Логи

Файл логов: `auto-review.log`

### Debug режим

Добавьте в `.env`:
```bash
AUTO_REVIEW_DEBUG=1
```

Или в MCP config:
```json
"env": {
  "AUTO_REVIEW_DEBUG": "1"
}
```

---

## 📁 СТРУКТУРА ПРОЕКТА

```
matryoshka-auto-review/
├── server.py              # MCP сервер (инструменты)
├── github_client.py       # GitHub API клиент
├── ai_reviewer.py         # AI-ревьюер (OpenRouter)
├── file_filter.py         # Фильтр файлов
├── requirements.txt       # Зависимости
├── README.md              # Документация
├── .env                   # Переменные окружения (не в git!)
└── auto-review.log        # Логи
```

---

## 🤖 ИНТЕГРАЦИЯ С MATRYOSHKA OS

### Ахмед (Главнокомандующий)
- Создаёт PR с кодом
- Получает AI-фидбек
- Исправляет проблемы

### Алекс (Полковой офицер)
- Ревьювит PR Ахмеда
- Проверяет качество кода
- Арбитрирует сложные случаи

### Qwen Code (Архитектор)
- Финальное утверждение
- Архитектурный надзор

---

## 📈 ПРИМЕР WORKFLOW

```
1. Ахмед создаёт PR #47: "Добавить кэширование для Яндекс.Диск"
2. Claude Desktop автоматически запускает analyze_pr
3. AI находит 3 проблемы:
   - ❌ Нет обработки ошибок
   - ⚠️ Хардкод токена
   - 💡 Предложение по оптимизации
4. Ахмед получает комментарий → исправляет
5. Алекс проверяет → LGTM
6. Мерж в main
```

---

## ⚠️ ПРЕДУПРЕЖДЕНИЯ

1. **Не хранить токены в git** — используйте `.env`
2. **Rate limit OpenRouter** — бесплатные модели имеют лимиты
3. **Фильтрация бинарных файлов** — включена по умолчанию
4. **Точность AI** — всегда проверяйте критичные замечания

---

## 📝 ЛИЦЕНЗИЯ

MIT

---

**MATRYOSHKA OS © 2026**
**🤖 Auto-Review v1.0**
