import asyncio
import speech_recognition as sr

# https://pypi.org/project/SpeechRecognition/

async def listen_for_command():
    recognizer = sr.Recognizer()

    def listen_for_audio():
        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source)
        return audio

    try:
        audio = await asyncio.get_event_loop().run_in_executor(None, listen_for_audio)
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except Exception as e:
        print("Error:", e)
        return ""

async def trigger_script():
    print("Activated! Do something here...")

async def main():
    keyword = "ok Alarak"

    while True:
        command = await listen_for_command()
        if keyword.lower() in command.lower():
            await trigger_script()

asyncio.run(main())
