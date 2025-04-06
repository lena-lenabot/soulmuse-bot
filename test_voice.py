import speech_recognition as sr

recognizer = sr.Recognizer()

with sr.AudioFile("./voice_message.ogg") as source:
    audio = recognizer.record(source)

try:
    text = recognizer.recognize_google(audio, language="ru-RU")
    print("✅ Распознанный текст:", text)
except Exception as e:
    print("❌ Ошибка при распознавании:", e)
