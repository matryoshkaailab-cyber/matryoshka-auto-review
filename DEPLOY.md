# 🚀 MATRYOSHKA AUTO-REVIEW - ИНСТРУКЦИЯ ПО РАЗВЁРТЫВАНИЮ

## 📋 ШАГ 1: СОЗДАТЬ РЕПОЗИТОРИЙ НА GITHUB

### Вариант A: Через GitHub UI
1. Перейдите на [github.com/new](https://github.com/new)
2. Название: `matryoshka-auto-review`
3. Описание: `AI-powered automated code review for MATRYOSHKA OS`
4. **Public** или **Private** (на ваше усмотрение)
5. ✅ **Initialize with README** — НЕ ставьте галочку!
6. Нажмите **Create repository**

### Вариант B: Через GitHub CLI
```bash
gh repo create matryoshka-auto-review --public --description "AI-powered automated code review for MATRYOSHKA OS"
```

---

## 📋 ШАГ 2: ЗАПУШИТЬ КОД

```bash
cd c:\matryoshka\auto-review

# Добавьте удалённый репозиторий (замените YOUR_USERNAME на ваш логин GitHub)
git remote add origin https://github.com/YOUR_USERNAME/matryoshka-auto-review.git

# Проверьте подключение
git remote -v

# Запушьте
git push -u origin master
```

**Если используете SSH:**
```bash
git remote add origin git@github.com:YOUR_USERNAME/matryoshka-auto-review.git
git push -u origin master
```

---

## 📋 ШАГ 3: НАСТРОИТЬ GITHUB SECRETS

### 3.1 GitHub Token (для workflow)

GitHub Actions автоматически создаёт `GITHUB_TOKEN` — ничего делать не нужно!

### 3.2 OpenRouter API Key

1. Перейдите в репозиторий на GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret**
4. Заполните:
   - **Name:** `OPENROUTER_API_KEY`
   - **Value:** `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`
5. Нажмите **Add secret**

### 3.3 (Опционально) Модель

1. **Settings** → **Secrets and variables** → **Actions** → **Variables**
2. **New repository variable**
3. Заполните:
   - **Name:** `OPENROUTER_MODEL`
   - **Value:** `nvidia/nemotron-3-super-120b-a12b:free`
4. Нажмите **Add variable**

---

## 📋 ШАГ 4: ПРОВЕРИТЬ WORKFLOW

1. Перейдите во вкладку **Actions** в репозитории
2. Убедитесь, что workflow `AI Code Review` отображается
3. Создайте тестовый PR:
   - Создайте ветку: `git checkout -b test-branch`
   - Внесите изменения в любой файл
   - Закоммитьте: `git commit -am "test: тестовые изменения"`
   - Запушьте: `git push origin test-branch`
   - Создайте PR на GitHub

---

## 📋 ШАГ 5: НАСТРОИТЬ CLAUDE DESKTOP (MCP)

### Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "matryoshka-auto-review": {
      "command": "python",
      "args": ["C:\\matryoshka\\auto-review\\server.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_personal_token_here",
        "GITHUB_REPO": "YOUR_USERNAME/matryoshka-auto-review",
        "OPENROUTER_API_KEY": "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",
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
        "GITHUB_TOKEN": "ghp_your_personal_token_here",
        "GITHUB_REPO": "YOUR_USERNAME/matryoshka-auto-review",
        "OPENROUTER_API_KEY": "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"
      }
    }
  }
}
```

**⚠️ ВАЖНО:** Для MCP нужен **Personal Access Token** (не GITHUB_TOKEN из Actions):

1. [github.com/settings/tokens](https://github.com/settings/tokens)
2. **Generate new token (classic)**
3. Скоупы: ✅ `repo` (Full control)
4. Скопируйте и вставьте в конфиг

---

## 📋 ШАГ 6: ТЕСТИРОВАНИЕ

### Тест 1: MCP Tools в Claude Desktop

Откройте Claude Desktop и напишите:

```
Покажи открытые PR в репозитории matryoshka-auto-review
```

Ожидаемый результат:
```
📋 **Открытые Pull Request'ы:**

**#1: test branch**
- Автор: @YOUR_USERNAME
- Создан: 2026-03-24T...
- Статус: open
- URL: https://github.com/YOUR_USERNAME/matryoshka-auto-review/pull/1
```

### Тест 2: AI Анализ PR

```
Проанализируй PR #1, найди проблемы
```

Ожидаемый результат:
```
🤖 **AI Review для PR #1: test branch**

🧠 Модель: nvidia/nemotron-3-super-120b-a12b:free
📁 Файлов: 1

📁 test.py [added]
...

📊 ИТОГО:
- Файлов: 1
- Critical: 0
- Warning: 0
- Suggestion: 1

✅ LGTM
```

### Тест 3: GitHub Actions

1. Откройте PR на GitHub
2. Перейдите во вкладку **Checks**
3. Убедитесь, что `AI Code Review` запустился
4. Через 1-2 минуты появится комментарий с AI-ревью

---

## 🔧 ДИАГНОСТИКА ПРОБЛЕМ

### Ошибка: "GITHUB_TOKEN not set"

**Решение:**
```bash
# Проверьте .env файл
cd c:\matryoshka\auto-review
cat .env

# Или добавьте переменную напрямую
set GITHUB_TOKEN=ghp_your_token_here
```

### Ошибка: "OPENROUTER_API_KEY not set"

**Решение:**
```bash
# Проверьте наличие ключа
set OPENROUTER_API_KEY

# Если пусто, добавьте
set OPENROUTER_API_KEY=sk-or-v1-...
```

### Ошибка: "Invalid repo format"

**Решение:** Убедитесь, что формат `owner/repo`:
```
✅ matryoshka/auto-review
❌ auto-review
❌ https://github.com/matryoshka/auto-review
```

### Workflow не запускается

**Решение:**
1. Проверьте **Actions** → **General** → **Actions permissions**
2. Убедитесь: ✅ **Allow all actions**
3. Проверьте Secrets (Settings → Secrets and variables → Actions)

---

## 📊 МОНИТОРИНГ

### Логи MCP сервера

```bash
cd c:\matryoshka\auto-review
type auto-review.log
```

### Логи GitHub Actions

1. Репозиторий → **Actions**
2. Выберите запуск workflow
3. Разверните логи шагов

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

### 1. Добавить в другие репозитории

Скопируйте workflow в другие проекты:

```bash
# В другом репозитории
mkdir -p .github/workflows
copy c:\matryoshka\auto-review\.github\workflows\auto-review.yml .github/workflows/
```

### 2. Настроить кастомные правила

Отредактируйте `file_filter.py`:
```python
REVIEW_EXTENSIONS.add('.your_extension')
IGNORE_EXTENSIONS.add('.ignore_this')
```

### 3. Интеграция с MATRYOSHKA OS

Добавьте MCP сервер в основной конфиг:

**c:\matryoshka\.qwen\settings.json:**
```json
{
  "mcpServers": {
    "matryoshka-auto-review": {
      "command": "python",
      "args": ["c:\\matryoshka\\auto-review\\server.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_...",
        "GITHUB_REPO": "matryoshka/matryoshka",
        "OPENROUTER_API_KEY": "sk-or-v1-..."
      }
    }
  }
}
```

---

## ✅ ЧЕКЛИСТ ЗАВЕРШЕНИЯ

- [ ] Репозиторий создан на GitHub
- [ ] Код запушен
- [ ] Secrets настроены (OPENROUTER_API_KEY)
- [ ] Workflow работает (проверить в Actions)
- [ ] Claude Desktop настроен (MCP config)
- [ ] Тестовый PR создан и проанализирован
- [ ] Сохранено в MCP Memory

---

**🫡 MATRYOSHKA AUTO-REVIEW ГОТОВ К РАБОТЕ!**
