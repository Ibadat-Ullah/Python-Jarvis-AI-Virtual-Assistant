import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import speech_recognition as sr
import webbrowser
import requests
import os
from gtts import gTTS
from playsound import playsound
from datetime import datetime
from groq import Groq
import tempfile
import soundLibrary

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "").strip()

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
recognizer = sr.Recognizer()


def setup_microphone():
    try:
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if d.get("max_input_channels", 0) > 0:
                sd.default.device = (i, None)
                print(f"Mic selected: {d['name']}")
                return
    except Exception as e:
        print("Mic setup error:", e)


setup_microphone()


def speak(text):
    try:
        if not text:
            return

        file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "jarvis_tts.mp3"
        )
        gTTS(text=text, lang="en").save(file)
        playsound(file)
        os.remove(file)

    except Exception as e:
        print("Speech Error:", repr(e))


def listen():
    try:
        print("Listening...")

        fs = 44100
        duration = 5

        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
        sd.wait()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav.write(tmp.name, fs, recording)

            with sr.AudioFile(tmp.name) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)

        os.remove(tmp.name)
        return text

    except sr.UnknownValueError:
        return None

    except sr.RequestError:
        return "ERROR"

    except Exception as e:
        print("Listen Error:", repr(e))
        return "ERROR"


def ai_process(command):
    try:
        if client is None:
            return "AI is currently unavailable"

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are Jarvis, a helpful assistant. Keep answers short and clear.",
                },
                {"role": "user", "content": command},
            ],
        )
        return response.choices[0].message.content

    except Exception as e:
        print("GROQ ERROR:", repr(e))
        return "AI is currently unavailable"


def process_command(c):
    c = c.lower()
    print("Command:", c)

    if "youtube" in c:
        speak("Opening YouTube")
        webbrowser.open("https://youtube.com")

    elif "google" in c:
        speak("Opening Google")
        webbrowser.open("https://google.com")

    elif "facebook" in c:
        speak("Opening Facebook")
        webbrowser.open("https://facebook.com")

    elif "linkedin" in c:
        speak("Opening LinkedIn")
        webbrowser.open("https://linkedin.com")

    elif c.startswith("play"):
        try:
            parts = c.split()
            if len(parts) < 2:
                speak("Tell me what to play")
                return
            key = parts[1].lower()
            link = soundLibrary.sound.get(key)
            if link:
                speak(f"Playing {key}")
                webbrowser.open(link)
            else:
                speak("Sound not found")
        except Exception as e:
            print("Play Error:", e)
            speak("Invalid play command")

    elif "time" in c:
        speak(datetime.now().strftime("%H:%M:%S"))

    elif "news" in c:
        try:
            if not NEWS_API_KEY:
                speak("News API key is missing")
                return

            url = (
                f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
            )
            r = requests.get(url, timeout=5)
            articles = r.json().get("articles", [])
            speak("Top headlines")
            for a in articles[:3]:
                speak(a["title"])
        except Exception as e:
            print("News Error:", e)
            speak("News error")

    elif "exit" in c or "stop" in c:
        speak("Goodbye")
        raise SystemExit(0)

    else:
        speak(ai_process(c))


speak("Jarvis is starting")

while True:
    voice = listen()

    if not voice or voice == "ERROR":
        continue

    print("≡ƒùú You said:", voice)

    if "jarvis" in voice.lower():
        speak("Yes, I am listening")

        while True:
            cmd = listen()
            if cmd and cmd != "ERROR":
                process_command(cmd)
