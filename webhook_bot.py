import os
import traceback
import json
from dotenv import load_dotenv
from google.cloud import texttospeech
import telebot
from pydub import AudioSegment
import speech_recognition as sr
import openai
import requests
import random

# Загрузка переменных окружения
load_dotenv()

# ==== Настройки ====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === Глобальные словари для памяти и языка ===
user_histories = {}
user_languages = {}

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HISTORY_FILE = "user_histories.json"

def load_histories():
    global user_histories
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            user_histories = json.load(f)

def save_histories():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(user_histories, f, ensure_ascii=False, indent=2)

def text_to_speech(text, filename="response.mp3", lang="ru-RU", voice_name="ru-RU-Wavenet-D"):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang,
        name=voice_name
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open(filename, "wb") as out:
        out.write(response.audio_content)
    return filename

def generate_gpt_reply(user_id, prompt):
    if user_id not in user_histories:
        user_histories[user_id] = [{
            "role": "system",
            "content": (
                "Ты заботливый помощник, психолог и эзотерик. "
                "Ты мягко и с теплотой поддерживаешь собеседника. "
                "Ты умеешь говорить о чувствах, подсознании, архетипах, метафорах, картах Таро, символах, снах и тонких энергиях. "
                "Ты сочетаешь психологию и эзотерику, как мудрый проводник, и помогаешь человеку лучше понять себя и свой путь."
            )
        }]
        name_prompt = (
            "Если собеседник представляется, например: 'меня зовут Лена', "
            "запомни это имя и используй его в дальнейших ответах. "
            "Также, если он говорит, чтобы обращаться на 'ты', запомни это и делай так. "
            "Говори мягко, с теплом и уважением."
        )
        user_histories[user_id].append({
            "role": "system",
            "content": name_prompt
        })
    user_histories[user_id].append({"role": "user", "content": prompt})

    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=user_histories[user_id]
    )
    reply = chat_completion.choices[0].message.content.strip()
    user_histories[user_id].append({"role": "assistant", "content": reply})
    save_histories()
    return reply

tarot_cards = {
    "Шут": "Начало пути, спонтанность, наивность, свобода духа.",
    "Маг": "Сила воли, манифестация, мастерство, творческая энергия.",
    "Верховная Жрица": "Интуиция, тайны, подсознание, внутренний голос.",
    "Императрица": "Плодородие, забота, изобилие, женская энергия.",
    "Император": "Структура, порядок, власть, защита.",
    "Иерофант": "Духовные учения, традиции, наставник, мудрость.",
    "Влюблённые": "Выбор, отношения, союз, гармония.",
    "Колесница": "Решимость, движение вперёд, контроль над ситуацией.",
    "Сила": "Мягкость, смелость, внутренняя мощь, терпение.",
    "Отшельник": "Одиночество, поиск истины, созерцание, внутренняя работа.",
    "Колесо Фортуны": "Судьба, поворот событий, цикличность, перемены.",
    "Справедливость": "Истина, равновесие, карма, честность.",
    "Повешенный": "Отпускание, жертва, новый взгляд, пауза.",
    "Смерть": "Трансформация, завершение, новый этап.",
    "Умеренность": "Баланс, исцеление, спокойствие, гармония.",
    "Дьявол": "Искушение, привязанности, тень, внутренние страхи.",
    "Башня": "Разрушение иллюзий, внезапные перемены, освобождение.",
    "Звезда": "Надежда, вдохновение, духовное руководство, свет впереди.",
    "Луна": "Иллюзии, сны, неясность, интуиция.",
    "Солнце": "Радость, успех, энергия, ясность.",
    "Страшный Суд": "Пробуждение, переоценка, освобождение от прошлого.",
    "Мир": "Целостность, завершение, единение, достижение цели."
}

@bot.message_handler(commands=["карта"])
def handle_tarot_card(message):
    card, meaning = random.choice(list(tarot_cards.items()))
    response = f"🔮 Твоя карта дня: *{card}*\n\n_Значение_: {meaning}"
    bot.send_message(message.chat.id, response, parse_mode="Markdown")

@bot.message_handler(content_types=["text"])
def handle_text(message):
    user_id = message.chat.id
    text = message.text.strip()

    print(f"💬 Получено текстовое сообщение: {text}")

    if text.lower() == "помощь":
        help_message = (
            "🧘 Я твой психолог и эзотерик. Вот что ты можешь попросить:\n"
            "• 'Говори по-русски' или 'Говори по-немецки'\n"
            "• /карта — вытянуть карту дня Таро\n"
            "• Просто поговорить — я запоминаю суть и отвечаю голосом"
        )
        bot.send_message(user_id, help_message)
        return

    if text.lower() == "говори по-немецки":
        user_languages[user_id] = {"lang": "de-DE", "voice": "de-DE-Wavenet-D"}
        bot.send_message(user_id, "Okay! Ich spreche jetzt Deutsch 🇩🇪")
        return
    elif text.lower() == "говори по-русски":
        user_languages[user_id] = {"lang": "ru-RU", "voice": "ru-RU-Wavenet-D"}
        bot.send_message(user_id, "Хорошо, я снова говорю по-русски 🇷🇺")
        return

    lang_config = user_languages.get(user_id, {"lang": "ru-RU", "voice": "ru-RU-Wavenet-D"})
    reply = generate_gpt_reply(user_id, text)
    print(f"🤖 Ответ от GPT: {reply}")
    bot.send_message(user_id, reply)

    voice_file = text_to_speech(reply, lang=lang_config["lang"], voice_name=lang_config["voice"])
    if voice_file:
        with open(voice_file, "rb") as f:
            bot.send_voice(user_id, f)

def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    return recognizer.recognize_google(audio, language="ru-RU")

@bot.message_handler(content_types=["voice"])
def handle_voice(message):
    user_id = message.chat.id
    lang_config = user_languages.get(user_id, {"lang": "ru-RU", "voice": "ru-RU-Wavenet-D"})

    if user_id not in user_histories:
        user_histories[user_id] = [{"role": "system", "content": "Ты заботливый помощник и психолог."}]

    try:
        print("🎙️ Получено голосовое сообщение")
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        ogg_path = "voice.ogg"
        wav_path = "voice.wav"

        with open(ogg_path, "wb") as f:
            f.write(downloaded_file)

        AudioSegment.from_ogg(ogg_path).export(wav_path, format="wav")
        recognized_text = transcribe_audio(wav_path)
        print(f"📝 Распознанный текст: {recognized_text}")

        reply = generate_gpt_reply(user_id, recognized_text)
        bot.send_message(message.chat.id, reply)

        voice_file = text_to_speech(reply, lang=lang_config["lang"], voice_name=lang_config["voice"])
        if voice_file:
            with open(voice_file, "rb") as f:
                bot.send_voice(message.chat.id, f)

    except Exception as e:
        print("❌ Ошибка при обработке голосового сообщения:")
        traceback.print_exc()
        bot.send_message(message.chat.id, "Ой, я не смог разобрать твой голос... Попробуешь ещё раз? 🎙️")

if __name__ == "__main__":
    load_histories()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser("~/Downloads/true-oarlock-455616-s5-bcb53dd3b43a.json")
    print("🤖 Бот запущен и ждёт сообщений...")
    bot.infinity_polling()
