# 🤖 MATRYOSHKA TELEGRAM BOTS — ВОССТАНОВЛЕНИЕ v6

**Дата:** 25 марта 2026 г.
**Статус:** ✅ РАБОТАЕТ
**Сервер:** 213.165.216.253 (Яндекс Облако)

---

## 📋 ОБЗОР

Система из 3 Telegram ботов на базе универсального образа matryoshka_bot:v6:

| Бот | Username | Владелец | Статус |
|-----|----------|----------|--------|
| **Алекс** | @oleg_industry_bot | Олег Чут (1951845052) | ✅ v6 |
| **Эклер** | @ZarnyAlexaBot | Наталья Чут (461605744) | ✅ v6 |
| **Алина** | @NikAvreliiBot | Николай (146881168) | ✅ v6 |

---

## 🏗️ АРХИТЕКТУРА

```
Telegram → Docker Container (matryoshka_bot:v6) → OpenRouter AI → Ответ
                 ↓
           SOUL.md (личность)
                 ↓
           История: 5 сообщений
```

**Модель:** nvidia/nemotron-3-super-120b-a12b:free (120B MoE, бесплатно)

---

## 🚀 БЫСТРЫЙ СТАРТ

### 1. Подготовка файлов

```bash
# На сервере (Ubuntu)
cd /home/ubuntu

# Файлы бота:
# - matryoshka_bot.py
# - Dockerfile.matryoshka_bot
# - {bot}_soul.md, {bot}_user.md, {bot}_memory.md
# - skills/ (12 навыков)
```

### 2. Сборка образа

```bash
docker build -t matryoshka_bot:v6 -f Dockerfile.matryoshka_bot .
```

### 3. Запуск бота

```bash
# Шаблон:
docker run -d --name {bot}_bot \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN={TOKEN} \
  -e ALLOWED_USERS={CHAT_ID} \
  -e OPENROUTER_API_KEY={KEY} \
  -e MODEL=nvidia/nemotron-3-super-120b-a12b:free \
  -v /home/ubuntu/{bot}_soul.md:/alex_soul.md \
  -v /home/ubuntu/{bot}_user.md:/alex_user.md \
  -v /home/ubuntu/{bot}_memory.md:/alex_memory.md \
  -v /home/ubuntu/skills:/skills \
  matryoshka_bot:v6
```

### 4. Проверка

```bash
# Статус
docker ps --format 'table {{.Names}}\t{{.Status}}'

# Логи
docker logs {bot}_bot --tail 20
```

---

## 🔧 ИСПРАВЛЕНИЯ v6

### Проблемы v1-v5:
1. ❌ 400 Bad Request — Telegram отклонял сообщения
2. ❌ Долгий ответ — история 20 сообщений
3. ❌ AI путался — длинный промпт (SOUL+USER+MEMORY)
4. ❌ Файлы не читались — только ссылки
5. ❌ Голосовые игнорировались

### Решения v6:
1. ✅ Убран parse_mode — чистый текст
2. ✅ История сокращена до 5 сообщений
3. ✅ Только SOUL.md + "ОТВЕЧАЙ БЫСТРО, КРАТКО, ПО ДЕЛУ"
4. ✅ get_file_content() — скачивание и чтение файлов
5. ✅ Поддержка voice, document, photo

---

## 🎯 ФУНКЦИОНАЛЬНОСТЬ v6

### Поддерживаемые типы сообщений:

**Текст:**
```
Пользователь: Привет
Бот: Привет! Чем помочь?
```

**Голосовые:**
```
[Голосовое сообщение]
Бот: [Скачивает → читает содержимое → отвечает]
```

**Документы:**
```
[Файл: document.txt]
Бот: [Скачивает → читает текст → анализирует → отвечает]
```

**Фото:**
```
[Фото]
Бот: [Скачивает → распознаёт → описывает]
```

---

## 🐛 ДИАГНОСТИКА

### Бот не отвечает

```bash
# Проверка контейнера
docker ps | grep {bot}_bot

# Если Restarting — смотрим логи
docker logs {bot}_bot --tail 50

# Перезапуск
docker rm -f {bot}_bot
docker run -d --name {bot}_bot ... (см. выше)
```

### 400 Bad Request

```
Причина: Telegram отклоняет сообщение
Решение: Убран parse_mode (HTML/Markdown) — чистый текст
```

### Долгий ответ

```
Причина: История >5 сообщений или длинный промпт
Решение: v6 — история 5, только SOUL.md
```

### Бот не читает файлы

```
Причина: Нет get_file_content()
Решение: v6 — скачивает и читает содержимое
```

---

## 🔑 API КЛЮЧИ (из .env)

```
TELEGRAM_BOT_TOKEN={BOT_TOKEN}
OPENROUTER_API_KEY={OPENROUTER_KEY}
YANDEX_STT/TTS={YANDEX_KEY}
YANDEX_DISK={YANDEX_DISK_KEY}
```

**Где взять:**
- Telegram: @BotFather → /mybots → API Token
- OpenRouter: openrouter.ai/keys
- Yandex: cloud.yandex.ru

---

## 📊 МЕТРИКИ

| Версия | Проблемы | Статус |
|--------|----------|--------|
| v1 | Python без requests | ❌ |
| v2 | 400 Bad Request | ❌ |
| v3 | SyntaxError | ❌ |
| v4 | HTML parse_mode | ❌ |
| v5 | Длинный промпт | ⚠️ |
| **v6** | **История 5, SOUL** | **✅** |

**Время ответа:** 5-15 секунд
**История:** 5 сообщений
**Промпт:** SOUL.md + краткая инструкция

---

## 📁 СТРУКТУРА ФАЙЛОВ

```
/home/ubuntu/
├── matryoshka_bot.py          # Код бота v6
├── Dockerfile.matryoshka_bot  # Docker образ
├── alex_soul.md               # Личность Алекса
├── alex_user.md               # Настройки Алекса
├── alex_memory.md             # Память Алекса
├── ekler_soul.md              # Личность Эклера
├── ekler_user.md              # Настройки Эклера
├── ekler_memory.md            # Память Эклера
├── alina_soul.md              # Личность Алины
├── alina_user.md              # Настройки Алины
├── alina_memory.md            # Память Алины
└── skills/                    # 12 навыков
    ├── YANDEX-DISK
    ├── YANDEX-STT
    ├── OCR
    └── ...
```

---

## 🚀 СЛЕДУЮЩИЕ ШАГИ

1. ✅ Запустить всех 3 ботов
2. ⏳ Тестирование голосовых (Yandex STT)
3. ⏳ Интеграция с n8n workflow
4. ⏳ Мониторинг и логи

---

**MATRYOSHKA OS v11.0 © 2026**
**Восстановление завершено ✅
