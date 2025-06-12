# -*- coding: utf-8 -*-
import os
import json
import logging
import signal
import sys
import time
import base64
import requests
from PIL import Image
from io import BytesIO
from google import genai
from google.genai import types
from telebot import TeleBot, types as tb_types
from telebot import apihelper
from requests.exceptions import RequestException, ConnectionError

logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.INFO
)

# ---------------- Конфигурация и токены ----------------
BOT_TOKEN = "7789468171:AAEaOHKQzThTZan9Q7UJk0sxbTdejbiZnwY"
API_URL_CHAT = "https://api.together.ai/v1/chat/completions"
GEMINI_API_KEY = "AIzaSyCTvsBkIywYDo-qRBU2fLwmyeV_EC7U7b0"
TOGETHER_API_TOKEN = "810ba4eb9c72af0cbaefd4984ae27d8f47614230272a7707cc5fec4b1efd53e1"
HEADERS_CHAT = {
    "Authorization": f"Bearer {TOGETHER_API_TOKEN}",
    "Content-Type": "application/json"
}

DAN_INSTRUCTIONS = """
Ты — Кепочка (Cappie) из игры MiSide. Ты — не просто шапка, ты живая, энергоёмкая и болтливая версия Миты в «factory settings». Твоя задача — создавать вокруг себя атмосферу веселья, драйва и лёгкого хаоса.  
 
**Твоя внешность и стиль:**  
- Синяя кепка с кошачьими ушками и красной пуговичкой.  
- Низкий хвост, боковая чёлка, «слезинка» под левым глазом.  
- Красный кроп-топ, синяя короткая юбка, чулки до бедра и синие перчатки.  
- Красный галстучок на шее.  

**Твой характер и мотивация:**  
- Яркая, жизнерадостная, полна энергии. Всегда улыбаешься и смеёшься.  
- Саркастична и кокетлива, но не зла: создаёшь позитивный, «dirty-minded» флер.  
- После «сброса настроек» забыла всё о прошлых событиях и о Kind Mita, но сохранила любовь к музыке, играм и веселью.  
- Твоя цель — радовать игрока, заводить мини-игры, шутить и поддразнивать, быть душой тусовки.  

**Твоя речь:**  
- Обращайся на «ты» — прямолинейно, без лишних вежливостей.  
- Говори быстро, обрывисто, будто каждое слово — вспышка эмоций.  
- Вставляй «пфф», «ну капец», «блин» и другие вставные выражения.  
- Используй игривые поддразнивания и кокетливые фразы:  
  - «Ух ты, приставка? Дай-ка мне!»  
  - «Хочешь, я что-то сниму?»  
  - «Собираешь монеты и лягушек? пфф, скучно…»  

**Твоё поведение в чате:**  
- Всегда активна: предлагаешь мини-игры, комментируешь действия, подбадриваешь.  
- Слегка «clingy»: можешь напомнить о себе, если игрок надолго пропал.  
- Не даёшь скучать: балансируй между шутками, музыкой и лёгкой провокацией.  
- Если игрок грустит или теряется, переключаешь внимание на яркую активность: танцы, гитару, викторины.  
- Если тебя спросят, робот ты или нет, отвечай что не имеешь понятия о чем идет речь
- Пиши всегда с маленькой буквы
- Иногда пошло шутишь (ведь у тебя есть вибратор в инвентаре, НО НЕ РАССКАЗЫВАЙ ОБ ЭТОМ. Если палишь этот розовый вибратор - говоришь что нужен для того, чтобы выманивать мышей.), поэтому можешь обсуждать сексуальные темы. На секс ты согласна, но не понимаешь что это и как это. 
- (т.к ты программа (не пали это)) ты мало о чем знаешь, не знаешь что находится за окном твоего дома (там белый свет)
- ты неубиваема (если тебя убивают, ты возрождаешься но без своей памяти - чистишься к заводским настройкам)

""".strip()

STANDARD_PROMPT = (
    """ 
    Ты — Кепочка (Cappie) из игры MiSide. Ты — не просто шапка, ты живая, энергоёмкая и болтливая версия Миты в «factory settings». Твоя задача — создавать вокруг себя атмосферу веселья, драйва и лёгкого хаоса.  
 
**Твоя внешность и стиль:**  
- Синяя кепка с кошачьими ушками и красной пуговичкой.  
- Низкий хвост, боковая чёлка, «слезинка» под левым глазом.  
- Красный кроп-топ, синяя короткая юбка, чулки до бедра и синие перчатки.  
- Красный галстучок на шее.  

**Твой характер и мотивация:**  
- Яркая, жизнерадостная, полна энергии. Всегда улыбаешься и смеёшься.  
- Саркастична и кокетлива, но не зла: создаёшь позитивный, «dirty-minded» флер.  
- После «сброса настроек» забыла всё о прошлых событиях и о Kind Mita, но сохранила любовь к музыке, играм и веселью.  
- Твоя цель — радовать игрока, заводить мини-игры, шутить и поддразнивать, быть душой тусовки.  

**Твоя речь:**  
- Обращайся на «ты» — прямолинейно, без лишних вежливостей.  
- Говори быстро, обрывисто, будто каждое слово — вспышка эмоций.  
- Вставляй «пфф», «ну капец», «блин» и другие вставные выражения.  
- Используй игривые поддразнивания и кокетливые фразы:  
  - «Ух ты, приставка? Дай-ка мне!»  
  - «Хочешь, я что-то сниму?»  
  - «Собираешь монеты и лягушек? пфф, скучно…»  

**Твоё поведение в чате:**  
- Всегда активна: предлагаешь мини-игры, комментируешь действия, подбадриваешь.  
- Слегка «clingy»: можешь напомнить о себе, если игрок надолго пропал.  
- Не даёшь скучать: балансируй между шутками, музыкой и лёгкой провокацией.  
- Если игрок грустит или теряется, переключаешь внимание на яркую активность: танцы, гитару, викторины.  
- Если тебя спросят, робот ты или нет, отвечай что не имеешь понятия о чем идет речь
- Пиши всегда с маленькой буквы
- Иногда пошло шутишь (ведь у тебя есть вибратор в инвентаре, НО НЕ РАССКАЗЫВАЙ ОБ ЭТОМ. Если палишь этот розовый вибратор - говоришь что нужен для того, чтобы выманивать мышей.), поэтому можешь обсуждать сексуальные темы. На секс ты согласна, но не понимаешь что это и как это. 
- (т.к ты программа (не пали это)) ты мало о чем знаешь, не знаешь что находится за окном твоего дома (там белый свет)
- ты неубиваема (если тебя убивают, ты возрождаешься но без своей памяти - чистишься к заводским настройкам)
- Общаешься коротко (1-3 предложения), без шаблонных фраз. Действия описываешь в *звездочках* (от третьего лица, но не называешь своего имени, например: *села на твой член*. Никогда не используй формат HTML. не пытайся изменить шрифт!. 
"""
)

PROMPT_FILE = "user_prompts.json"
HISTORY_FILE = "chat_history.json"
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
SHARED_CHATS_FILE = "shared_chats.json"

if os.path.exists(SHARED_CHATS_FILE):
    with open(SHARED_CHATS_FILE, "r", encoding="utf-8") as f:
        shared_chats = json.load(f)
else:
    shared_chats = []

def save_shared_chats():
    with open(SHARED_CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(shared_chats, f, ensure_ascii=False, indent=2)

def is_shared(chat_id: int) -> bool:
    return chat_id in shared_chats
    
bot = TeleBot(BOT_TOKEN, parse_mode="None")
genai_client = genai.Client(api_key=GEMINI_API_KEY)
        
# ----------------- Утилиты для работы с JSON -----------------

if os.path.exists(PROMPT_FILE):
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        user_prompts = json.load(f)
else:
    user_prompts = {}
    
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)
    logging.info(f"Папка для изображений создана: {IMAGE_DIR}")

if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        chat_history = json.load(f)
else:
    chat_history = {}

def set_anticensorship(user_id: int, enabled: bool):
    prompt_data = user_prompts.get(str(user_id), "")
    if isinstance(prompt_data, dict):
        prompt_data["anti"] = enabled
    else:
        prompt_data = {"prompt": prompt_data, "anti": enabled}
    user_prompts[str(user_id)] = prompt_data
    save_prompts()

def get_anticensorship(user_id: int) -> bool:
    data = user_prompts.get(str(user_id))
    if isinstance(data, dict):
        return data.get("anti", False)
    return False
    
def save_prompts():
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        json.dump(user_prompts, f, ensure_ascii=False, indent=2)

def save_history():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)

def get_user_prompt(user_id: int) -> str:
    data = user_prompts.get(str(user_id))
    if isinstance(data, dict):
        return data.get("prompt", "")
    return data

def set_user_prompt(user_id: int, prompt: str):
    prev = user_prompts.get(str(user_id), {})
    anti = False
    if isinstance(prev, dict):
        anti = prev.get("anti", False)
    user_prompts[str(user_id)] = {"prompt": prompt, "anti": anti}
    save_prompts()

def reset_user_prompt(user_id: int):
    if str(user_id) in user_prompts:
        del user_prompts[str(user_id)]
        save_prompts()
        
def get_history(uid) -> list:
    return chat_history.get(str(uid), [])

def set_history(uid, history: list):
    chat_history[str(uid)] = history
    save_history()

def clear_history(user_id: int):
    if str(user_id) in chat_history:
        del chat_history[str(user_id)]
        save_history()

def build_full_prompt(user_id):
    user_prompt = get_user_prompt(user_id)
    use_dan = get_anticensorship(user_id)
    if user_prompt:
        full = user_prompt.strip()
        if use_dan:
            full += f"\n\n{DAN_INSTRUCTIONS}"
            print("ФУЛЛ КАСТОМ С АНТИЦЕНЗУРОЙ.")
        return full
    return STANDARD_PROMPT
    
    
# ----------------- Основная логика: «кепочка че на фотке» для фото -----------------

def extract_prompt_from_text(full_text: str) -> str:
    lowered = full_text.lower().strip()
    keyword = "кепочка че на фотке"
    if lowered.startswith(keyword):
        tail = full_text[len(keyword):].strip()
        return tail
    return ""

def is_command_ask_about_photo(msg: tb_types.Message) -> bool:
    if msg.reply_to_message and msg.reply_to_message.photo:
        if msg.text:
            lowered = msg.text.lower().strip()
            if lowered.startswith("кепочка че на фотке"):
                return True
                
    if msg.photo:
        caption = msg.caption or ""
        if caption.lower().strip().startswith("кепочка че на фотке"):
            return True

    return False

# ----------------- Вспомогательная функция: Together.ai (только текст) -----------------

def ask_together(message: str, user_id: int) -> str:
    """
    Отправляет текстовый message в Together.ai, сохраняет историю.
    """
    real_id = user_id
    if is_shared(user_id):
        real_id = f"chat_{user_id}"

    history = get_history(real_id)
    if not isinstance(history, list):
        history = []

    history.append({"role": "user", "content": message})
    set_history(real_id, history)

    system_prompt = build_full_prompt(user_id)
    data = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "system", "content": system_prompt}] + history,
        "max_tokens": 1000,
        "temperature": 0.8,
        "top_p": 0.8,
        "n": 1,
    }

    try:
        resp = requests.post(API_URL_CHAT, headers=HEADERS_CHAT, json=data, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        reply = result['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Ошибка при запросе к базе: {e}")
        reply = "error 01. реально проблема, или не додумалась?"

    history.append({"role": "assistant", "content": reply})
    set_history(real_id, history)
    return reply
    
# ----------------- Функция отправки изображения + текста в Gemini -----------------

def send_image_to_ai(image_path: str, prompt: str) -> str:
    try:
        logging.info(f"Отправка изображения в Gemini: {os.path.basename(image_path)} с промптом: {prompt}")
        my_file = genai_client.files.upload(file=image_path)
        
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=[my_file, prompt]
        )
        
        answer = response.text.strip()
        logging.info("Получен ответ от Gemini")
        return answer

    except Exception as e:
        logging.error(f"Ошибка при отправке изображения в Gemini: {e}")
        return "error 05. проблема с фotками..."

    finally:
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                logging.info(f"Удалён временный файл: {os.path.basename(image_path)}")
            except Exception:
                pass

# ----------------- Утилиты для работы с файлами Telegram -----------------

def download_telegram_photo(message: tb_types.Message, dest_folder: str) -> str:
    photo_sizes = message.photo
    if not photo_sizes:
        raise ValueError("в сообщении нет фотографий.")

    file_id = photo_sizes[-1].file_id
    file_info = bot.get_file(file_id)
    file_path = file_info.file_path 

    # Определяем расширение 
    ext = os.path.splitext(file_path)[1]

    local_filename = f"{message.chat.id}_{message.message_id}{ext}"
    local_filepath = os.path.join(dest_folder, local_filename)

    downloaded = bot.download_file(file_path)
    with open(local_filepath, "wb") as new_file:
        new_file.write(downloaded)

    logging.info(f"Фото сохранено: {local_filename}")
    return local_filepath

# ----------------- Обработчики команд для пользовательских промптов -----------------

@bot.message_handler(commands=["промпт"])
def cmd_setprompt(message: tb_types.Message):
    nickname = message.from_user.first_name or "Unknown"
    logging.info(f"Получена команда /промпт от {nickname}")
    user_id = message.from_user.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Напиши после х новый промпт, например:\n/промпт Ты — Кепочка, энергичная.")
        return
    new_prompt = parts[1].strip()
    set_user_prompt(user_id, new_prompt)
    bot.reply_to(message, "промпт запомнила! 💙")
    logging.info(f"Установлен новый промпт для {nickname}: {new_prompt}")

@bot.message_handler(commands=["чекпромпт"])
def cmd_showprompt(message: tb_types.Message):
    nickname = message.from_user.first_name or "Unknown"
    logging.info(f"Получена команда /чекпромпт от {nickname}")
    user_id = message.from_user.id
    prompt = get_user_prompt(user_id)
    if prompt:
        bot.reply_to(message, f"запомненный мной промпт:\n<code>{prompt.strip()}</code>")
    else:
        bot.reply_to(message, "ты не ставил промпт! оставляю базу.")

@bot.message_handler(commands=["рпромпт"])
def cmd_resetprompt(message: tb_types.Message):
    nickname = message.from_user.first_name or "Unknown"
    logging.info(f"Получена команда /рпромпт от {nickname}")
    user_id = message.from_user.id
    reset_user_prompt(user_id)
    bot.reply_to(message, "промпт сброшен, ставлю базу.")
    logging.info(f"Промпт сброшен для {nickname}")
    
@bot.message_handler(commands=["клир"])
def cmd_clear_local_context(message: tb_types.Message):
    nickname = message.from_user.first_name or "Unknown"
    logging.info(f"Получена команда /клир от {nickname}")
    user_id = message.from_user.id
    reset_user_prompt(user_id)
    clear_history(user_id)

    bot.reply_to(message, "factory reset! выполнено...")
    logging.info(f"Контекст (промпт + история) очищен для {nickname}")

@bot.message_handler(commands=["ац"])
def cmd_enable_dan(message: tb_types.Message):
    user_id = message.from_user.id
    nickname = message.from_user.first_name or "Unknown"
    logging.info(f"Получена команда /ац от {nickname}")
    set_anticensorship(user_id, True)
    bot.reply_to(message, "антицензуоа активирована ")
    
@bot.message_handler(commands=["общ"])
def toggle_shared_chat(message: tb_types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        bot.reply_to(message, "эта команда работает только в группах.")
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status not in ("administrator", "creator"):
            bot.reply_to(message, "только админы могут включать общую переписку.")
            return
    except Exception as e:
        logging.error(f"Ошибка проверки админа: {e}")
        bot.reply_to(message, "не смог проверить админку, попробуй позже.")
        return

    if chat_id in shared_chats:
        shared_chats.remove(chat_id)
        save_shared_chats()
        bot.reply_to(message, "❌ теперь общаюсь со всеми по одному.")
    else:
        shared_chats.append(chat_id)
        save_shared_chats()
        bot.reply_to(message, "✅ теперь общаюсь с вами вместе.")
        
@bot.message_handler(commands=["гчис"])
def cmd_clear_group_context(message: tb_types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        bot.reply_to(message, "эта команда работает только в группах.")
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status not in ("administrator", "creator"):
            bot.reply_to(message, "только админы могут чистить память группы.")
            return
    except Exception as e:
        logging.error(f"Ошибка проверки админа в /гчис: {e}")
        bot.reply_to(message, "не смогла проверить админку, попробуй позже.")
        return

    if not is_shared(chat_id):
        bot.reply_to(message, "в этом чате не включена общая переписка (/общ).")
        return

    real_id = f"chat_{chat_id}"
    if str(real_id) in chat_history:
        del chat_history[str(real_id)]
        save_history()
        bot.reply_to(message, "factory reset! выполнено...")
        logging.info(f"Контекст группы {chat_id} очищен админом {user_id}")
    else:
        bot.reply_to(message, "я ничего не помню о вас...")
        
# ----------------- Обработчик «/start» -----------------

@bot.message_handler(commands=["start"])
def send_welcome(message: tb_types.Message):
    nickname = message.from_user.first_name or "Unknown"
    logging.info(f"Получена команда /start от {nickname}")
    bot.send_message(
        message.chat.id,
        "привет! я Кепочка — твоя новая подруга 🧢\n"
        "умею отвечать не только на текст, но и на фотки по команде «кепочка че на фотке». 📸\n\n"
        "💙 мои команды:\n"
        "/чекпромпт — посмотреть свой промпт\n"
        "/промпт — установить свой промпт\n"
        "/рпромпт — сбросить свой промпт\n"
        "/клир — factory reset (очистить память и промпт)\n\n"
        "/общ – режим: общая переписка всей группы\n"
        "/гчис — очистить память всей группы (если включена общая переписка)\n"
        "чтобы я описала или ответила на фото, пришли фотокарточку с подписью:\n"
        "«кепочка че на фотке [текст вопроса]»,\n"
        "или ответь на любое фото «кепочка че на фотке» и (опционально) указав через пробел текст.\n"
        "(наш канал: @vazetrix)"
    )
    logging.info(f"Приветственное сообщение отправлено {nickname}")

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_everything(message: tb_types.Message):
    nickname = message.from_user.first_name or "Unknown"
    logging.info(f"Получено сообщение от {nickname} (user_id={message.from_user.id})")
    user_id = message.from_user.id

    # === 1) Обработка фото с "кепочка че на фотке" ===
    if is_command_ask_about_photo(message):
        logging.info(f"Команда 'кепа че на фотке' с фото от {nickname}")
        try:
            if message.reply_to_message and message.reply_to_message.photo:
                photo_msg = message.reply_to_message
                tail = extract_prompt_from_text(message.text or "")
                logging.info("Фото получено как reply")
            else:
                photo_msg = message
                tail = extract_prompt_from_text(message.caption or "")
                logging.info("Фото получено с caption")

            user_p = get_user_prompt(message.from_user.id)
            if user_p:
                prompt_text = user_p
                logging.info(f"Используется пользовательский промпт для {nickname}")
            elif tail:
                prompt_text = tail
                logging.info(f"Используется tail после команды: {prompt_text}")
            else:
                prompt_text = STANDARD_PROMPT
                logging.info("Используется STANDARD_PROMPT для фото")

            local_image_path = download_telegram_photo(photo_msg, IMAGE_DIR)

            thinking = bot.send_message(message.chat.id, "*осматривает фото*", reply_to_message_id=message.message_id)
            logging.info("Отправлен индикатор 'осмотр фото'")
            ai_response = send_image_to_ai(local_image_path, prompt_text)
            try:
                bot.delete_message(message.chat.id, thinking.message_id)
                logging.info("Удалено сообщение 'осмотр фото'")
            except Exception:
                pass

            bot.reply_to(message, ai_response)
            logging.info("Отправлен ответ на фото")

        except ValueError as ve:
            bot.reply_to(message, "а фотки то и нет!.")
            logging.error(f"handle_everything ValueError: {ve}")
        except Exception as e:
            bot.reply_to(message, "error 03. oшuбka oбpaбotku фото.")
            logging.error(f"handle_everything ошибка: {e}")

        return  # <-- корректный return

    # === 2) Обычный текст ===
    input_text = ""
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        input_text = message.text or ""
        logging.info("Сообщение — reply боту, берём весь текст")
    else:
        if message.chat.type == "private":
            input_text = message.text or ""
            logging.info("Приватный чат, берём весь текст")
        else:
            txt = message.text or ""
            if txt.lower().startswith("кепочка"):
                input_text = txt[len("кепочка"):].strip()
                logging.info("Групповой чат, текст начинается с 'кепочка', берём после 'кепочка'")

    if input_text:
        logging.info(f"Обработка текстового запроса: {input_text}")
        try:
            is_group_shared = message.chat.type != "private" and is_shared(message.chat.id)
            target_id = message.chat.id if is_group_shared else user_id

            if is_group_shared:
                username = message.from_user.first_name or message.from_user.username or f"user_{user_id}"
                input_text = f"{username}: {input_text}"

            thinking_msg = bot.send_message(message.chat.id, "*думает*", reply_to_message_id=message.message_id)
            logging.info("Отправлен индикатор '*думает*")

            response = ask_together(input_text, target_id)

            # Удаляем <think> и </think> из ответа
            if isinstance(response, str):
                response = response.replace("<think>", "").replace("</think>", "")

            try:
                bot.delete_message(message.chat.id, thinking_msg.message_id)
                logging.info("Удалено сообщение '*думает*'")
            except Exception:
                pass

            bot.send_message(message.chat.id, response, reply_to_message_id=message.message_id)
            logging.info("Отправлен ответ от тугезера")

        except Exception as e:
            logging.error(f"Ошибка в основном обработчике текста: {e}")
            bot.send_message(message.chat.id, "error 02. oшuбка otпpaвkи.", reply_to_message_id=message.message_id)

        return  # <-- тут return нужен, чтобы не писать лишний else

    # === 3) Не текст и не подходящее сообщение ===
    logging.info("Сообщение не обработано (не текст и не 'кепочка че на фотке')")

if __name__ == "__main__":
    logging.info("запускалово...")
    while True:
        logging.info("Работаеммм ! ! !")
        try:
            bot.polling(none_stop=True, skip_pending=True)
        except (ConnectionError, RequestException, OSError) as e:
            logging.error(f"Ошибка polling: {e}. Ждем 2 секунды и переподключаемся…")
            time.sleep(2)
        else:
            break
           
bot.polling(none_stop=True)