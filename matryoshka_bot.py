#!/usr/bin/env python3
"""
MATRYOSHKA OS - Bot (Telegram)
Поддержка: текст, голосовые, документы, фото
"""

import os
import sys
import requests
import logging
import time

# Настройки
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_USERS = os.getenv('ALLOWED_USERS', '').split(',')
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')
MODEL = os.getenv('MODEL', 'nvidia/nemotron-3-super-120b-a12b:free')

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bot')

# Telegram API URL
TELEGRAM_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

# История сообщений
message_history = {}

def get_updates(offset=None):
    """Получить обновления от Telegram"""
    url = f'{TELEGRAM_URL}/getUpdates'
    params = {'offset': offset, 'timeout': 30}
    try:
        response = requests.get(url, params=params, timeout=35)
        response.raise_for_status()
        return response.json().get('result', [])
    except Exception as e:
        logger.error(f'Error getting updates: {e}')
        return []

def send_message(chat_id, text, reply_to_message_id=None):
    """Отправить сообщение"""
    url = f'{TELEGRAM_URL}/sendMessage'
    data = {
        'chat_id': chat_id,
        'text': text,
        'disable_web_page_preview': True
    }
    if reply_to_message_id:
        data['reply_to_message_id'] = reply_to_message_id

    try:
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f'Error sending message: {e}')
        return None

def send_chat_action(chat_id, action='typing'):
    """Отправить индикатор набора текста"""
    url = f'{TELEGRAM_URL}/sendChatAction'
    data = {
        'chat_id': chat_id,
        'action': action
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.ok
    except Exception as e:
        logger.error(f'Error sending chat action: {e}')
        return None

def get_file_content(file_id):
    """Скачать содержимое файла"""
    url = f'{TELEGRAM_URL}/getFile'
    data = {'file_id': file_id}
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        result = response.json().get('result', {})
        file_path = result.get('file_path')
        if not file_path:
            return None
        
        # Скачиваем файл
        file_url = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}'
        file_response = requests.get(file_url, timeout=30)
        file_response.raise_for_status()
        
        # Пытаемся прочитать как текст
        try:
            content = file_response.text[:2000]  # Ограничиваем 2000 символов
            return content
        except:
            return f"[Файл: {result.get('file_size', 'unknown')} bytes]"
    except Exception as e:
        logger.error(f'Error getting file content: {e}')
        return None

def call_openrouter(messages, system_prompt=None):
    """Вызов OpenRouter API"""
    url = 'https://openrouter.ai/api/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENROUTER_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://matryoshka-digital.ru',
        'X-Title': 'MATRYOSHKA Bot'
    }

    all_messages = []
    if system_prompt:
        all_messages.append({'role': 'system', 'content': system_prompt})
    all_messages.extend(messages)

    data = {
        'model': MODEL,
        'messages': all_messages,
        'max_tokens': 2000,
        'temperature': 0.7
    }

    try:
        logger.info(f'OpenRouter request: model={MODEL}, messages={len(all_messages)}')
        response = requests.post(url, headers=headers, json=data, timeout=120)
        logger.info(f'OpenRouter response status: {response.status_code}')

        if response.status_code != 200:
            logger.error(f'OpenRouter error response: {response.text}')
            return f'❌ Ошибка AI: {response.status_code} - {response.text[:200]}'

        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f'OpenRouter error: {e}')
        return f'❌ Ошибка AI: {str(e)}'


def get_system_prompt():
    """Загрузить системный промпт — только SOUL для краткости"""
    try:
        # Пробуем загрузить из корня (для ekler_bot, alina_bot)
        with open('/alex_soul.md', 'r', encoding='utf-8') as f:
            soul = f.read()
        # Добавляем краткую инструкцию
        return f"{soul}\n\n⚡ ОТВЕЧАЙ БЫСТРО, КРАТКО, ПО ДЕЛУ. БЕЗ ВОДЫ."
    except Exception as e:
        logger.error(f'Error loading SOUL from root: {e}')
        try:
            with open('/home/node/.openclaw/workspaces/alex/SOUL.md', 'r', encoding='utf-8') as f:
                soul = f.read()
            return f"{soul}\n\n⚡ ОТВЕЧАЙ БЫСТРО, КРАТКО, ПО ДЕЛУ. БЕЗ ВОДЫ."
        except Exception as e2:
            logger.error(f'Error loading SOUL from workspace: {e2}')
            return "Ты — полезный ассистент. Отвечай быстро и по делу."

def process_message(message):
    """Обработка сообщения"""
    chat_id = message['chat']['id']
    user_id = message['from']['id']
    message_id = message['message_id']

    # Проверка пользователя
    if str(user_id) not in ALLOWED_USERS:
        send_message(chat_id, '❌ Доступ запрещён', reply_to_message_id=message_id)
        return

    # Инициализация истории
    if chat_id not in message_history:
        message_history[chat_id] = []

    # Загрузка системного промпта
    system_prompt = get_system_prompt()
    if not system_prompt:
        system_prompt = "Ты — помощник пользователя."

    # Обработка разных типов сообщений
    user_content = ""
    
    # Текст
    text = message.get('text', '')
    if text:
        user_content = text
    
    # Голосовое сообщение
    voice = message.get('voice')
    if voice:
        file_id = voice.get('file_id')
        content = get_file_content(file_id)
        if content:
            user_content = f"[ГОЛОСОВОЕ СООБЩЕНИЕ]\nСодержимое: {content}\n\n{text if text else 'Распознай это голосовое сообщение'}"
        else:
            user_content = "[ГОЛОСОВОЕ СООБЩЕНИЕ - не удалось распознать]"
    
    # Документ
    document = message.get('document')
    if document:
        file_id = document.get('file_id')
        file_name = document.get('file_name', 'unknown')
        content = get_file_content(file_id)
        if content:
            user_content = f"[ДОКУМЕНТ: {file_name}]\nСодержимое:\n{content}\n\n{text if text else 'Прочитай этот документ'}"
        else:
            user_content = f"[ДОКУМЕНТ: {file_name} - не удалось прочитать содержимое]"
    
    # Фото
    photo = message.get('photo', [])
    if photo:
        # Берём наибольшее фото
        file_id = photo[-1].get('file_id')
        content = get_file_content(file_id)
        if content:
            user_content = f"[ФОТО]\n{content}\n\n{text if text else 'Опиши это фото'}"
        else:
            user_content = "[ФОТО - не удалось распознать]"
    
    # Если ничего нет
    if not user_content:
        user_content = "[Пустое сообщение]"

    # Добавляем сообщение пользователя
    message_history[chat_id].append({'role': 'user', 'content': user_content})

    # Ограничиваем историю 5 сообщениями (чтобы AI не тормозил)
    if len(message_history[chat_id]) > 5:
        message_history[chat_id] = message_history[chat_id][-5:]

    # ОТПРАВЛЯЕМ TYPING INDICATOR!
    logger.info(f'Sending typing indicator to user {user_id}')
    send_chat_action(chat_id, 'typing')

    # Вызов AI
    logger.info(f'Calling OpenRouter for user {user_id}...')
    response = call_openrouter(message_history[chat_id], system_prompt)

    # Добавляем ответ AI
    message_history[chat_id].append({'role': 'assistant', 'content': response})

    # Отправка ответа с обработкой ошибок
    result = send_message(chat_id, response, reply_to_message_id=message_id)
    if result:
        logger.info(f'Response sent to user {user_id}')
    else:
        # Если не удалось отправить — пробуем упростить сообщение
        short_response = response[:1000] + "..." if len(response) > 1000 else response
        send_message(chat_id, f"⚠️ Ошибка формата. Краткий ответ:\n{short_response}", reply_to_message_id=message_id)
        logger.error(f'Failed to send full response, sent shortened version')

def main():
    """Основной цикл"""
    logger.info(f'🤖 Bot starting... (Model: {MODEL})')
    logger.info(f'Allowed users: {ALLOWED_USERS}')

    # Проверка бота
    try:
        response = requests.get(f'{TELEGRAM_URL}/getMe', timeout=10)
        bot_info = response.json().get('result', {})
        logger.info(f'Bot info: @{bot_info.get("username", "unknown")}')
    except Exception as e:
        logger.error(f'Cannot connect to Telegram: {e}')
        sys.exit(1)

    last_update_id = 0
    logger.info('Bot is running. Listening for messages...')

    while True:
        try:
            updates = get_updates(last_update_id + 1 if last_update_id else None)

            for update in updates:
                last_update_id = update['update_id']

                if 'message' in update:
                    process_message(update['message'])

        except KeyboardInterrupt:
            logger.info('Bot stopped by user')
            break
        except Exception as e:
            logger.error(f'Error in main loop: {e}')
            time.sleep(5)

if __name__ == '__main__':
    main()
