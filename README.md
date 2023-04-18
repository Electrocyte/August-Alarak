# August Alarak Telegram Bot

August Alarak is a versatile Telegram bot designed to transcribe audio to text, translate text, generate audio, and call GPT-3.5 models. The bot utilizes the OpenAI Whisper ASR system and ChatGPT along with ElevenLabs for text-to-speech functionality.

## Features

1. Transcribe audio files (MP3) to text
2. Polish transcripts using ChatGPT
3. Translate text between languages
4. Generate audio from text using ElevenLabs
5. Call GPT-3.5 models for various tasks

## Requirements

* Python 3.10+
* [openai](https://pypi.org/project/openai/) library
* [pydub](https://pypi.org/project/pydub/)
* [python-telegram-bot](https://pypi.org/project/python-telegram-bot/)
* [pyannote](https://github.com/pyannote)
* OpenAI API key
* Telegram Bot API key

## Installation

1. Clone this repository:

```bash
git clone https://github.com/Electrocyte/AugustAlarak.git
pip install pipenv

cd AugustAlarak
pipenv install
```

Create a file named bot_token in the repository root containing your Telegram Bot API token, and a file named api_key containing your OpenAI API key.

(Optional) Create a file named allowed_userID in the repository root containing a list of allowed user IDs, one per line. If this file is not provided, the bot will be accessible to all users.

## Usage

Run the bot:

```bash
cd AugustAlarak
pipenv shell
python ./telegram_audio.py -a "/api_key/location/AugustAlarak/" \
    -b "/bot_token/location/AugustAlarak/" \
    -o "/save/location/AugustAlarak/" \
    -s "live"
```

Start interacting with the bot on Telegram by sending the 

    /start command.

Send a voice message to the bot and it will return the transcribed text.

Use the various available commands:

    /translate - Translate text or audio to English
    
    /e2f - Translate English text to French
    
    /e2c - Translate English text to Chinese (with Pinyin)
    
    /e2m - Translate English text to Bahasa Melayu
    
    /say - Generate an audio file from text
    
    /gpt - Call GPT-3.5 models with a text prompt


<iframe width="100%" height="300" scrolling="no" frameborder="no" allow="autoplay" src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/1495280575&color=%2300ff2f&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true&visual=true"></iframe>

## Contributing

Feel free to open issues and submit pull requests for improvements and bug fixes.
