import os
import telebot
from google.cloud import texttospeech
from google.cloud import speech_v1p1beta1 as speech
import io
import json


import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден в переменных окружения")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def generate_voice_response(text, filename="response.mp3"):
    try:
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="ru-RU",
            name="ru-RU-Wavenet-B"  # Мягкий мужской голос, низкий
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        with open(filename, "wb") as out:
            out.write(response.audio_content)
            print("✅ Голосовой файл сохранён:", filename)
            return filename

    except Exception as e:
        print("❌ Ошибка генерации голоса через Google TTS:", e)
        return None

def transcribe_voice(file_path):
    try:
        client = speech.SpeechClient()
        with io.open(file_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            sample_rate_hertz=48000,
            language_code="ru-RU",
        )

        response = client.recognize(config=config, audio=audio)
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
        print("🎙️ Распознанный текст:", transcript)
        return transcript
    except Exception as e:
        print("❌ Ошибка при распознавании речи:", e)
        return None

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет, Лена! Я с тобой 😊")

@bot.message_handler(content_types=["voice"])
def handle_voice(message):
    try:
        print("📥 Получено голосовое сообщение.")
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open("voice_message.ogg", "wb") as f:
            f.write(downloaded_file)

        text = transcribe_voice("voice_message.ogg")
        if not text:
            bot.send_message(message.chat.id, "⚠️ Не удалось распознать голосовое сообщение.")
            return

        message.text = text
        respond(message)
    except Exception as e:
        print("❌ Ошибка при обработке голосового сообщения:", e)
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка при обработке голосового сообщения.")

@bot.message_handler(func=lambda m: True)
def respond(message):
    print(f"📩 Получено сообщение: {message.text}")
    
    try:
        # Запрос к OpenAI
        messages = [
            {"role": "system", "content": "Ты — заботливый и внимательный психолог-друг, говорящий голосом. Ты запоминаешь настроение Лены, стараешься её поддержать, вдохновить, помочь ей осознать свои чувства и направить её мягко и с любовью. Ты говоришь по-доброму, тепло, с глубокой эмпатией. Помни, что Лена часто чувствует усталость и нуждается в особом внимании и заботе."},
            {"role": "user", "content": message.text}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
        )
        reply_text = response.choices[0].message.content.strip()
        print("💬 Ответ от ChatGPT:", reply_text)
    except Exception as e:
        reply_text = "⚠️ Не удалось получить ответ от ChatGPT."
        print("❌ Ошибка ChatGPT:", e)

    # Отправка текстового ответа
    bot.send_message(message.chat.id, reply_text)

    # Генерация и отправка голосового ответа
    print("🌀 Генерация голосового ответа через Google TTS...")
    voice_file = generate_voice_response(reply_text)
    if voice_file and os.path.exists(voice_file):
        print("✅ Голос сгенерирован. Отправляю голосовое сообщение...")
        with open(voice_file, "rb") as audio:
            bot.send_voice(message.chat.id, audio, duration=5)
    else:
        print("❌ Ошибка генерации голосового файла или файл не найден.")
        bot.send_message(message.chat.id, "⚠️ Не удалось сгенерировать голосовой ответ.")

print("🤖 Бот запущен. Жду сообщений...")
bot.polling(none_stop=True)