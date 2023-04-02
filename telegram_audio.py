import logging
import os
import argparse
import openai
import whisper
import call_GPT
import elevenLabs
from telegram import Update
from typing import List
from pydub import AudioSegment
from functools import partial
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters


def read_allowed_uID(file_path: str = "allowed_userID") -> List[int]:
    with open(file_path, "r") as f:
        return [int(line) for line in f]


def read_bot_token(file_path: str = "bot_token") -> str:
    with open(file_path, "r") as f:
        return f.read()


def check_uID(update: Update, allowed_uIDs: List) -> bool:
    if len(allowed_uIDs) == 0:
        return True
    return update.effective_chat.id in allowed_uIDs


# The goal is to have this function called every time the Bot receives a Telegram message that contains the /start command.
async def start(allow_uID: List[int], update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    print(f"Chat ID: {chat_id}")
    if not check_uID(update, allow_uID):
        await context.bot.send_message(chat_id=update.effective_chat.id, \
                                   text=f"Your user ID: {update.effective_user.id}. Please use your own api key <3")
        return

    await context.bot.send_message(chat_id=update.effective_chat.id, \
                                   text=f"Send me a voice message and I'll send it back as an audio file! Your user ID: {update.effective_user.id}")


# async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await context.bot.send_message(chat_id=update.effective_chat.id, text = update.message.to_json())


async def voice_handler(allow_uID: List[int], botKeyPath: str, save_loc: str, prompt: str, save: str, \
                        update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Received message: {update.effective_user.id}, {update.message.chat_id}")
    if not check_uID(update, allow_uID):
        return

    # check that the send is human for transcription
    if update.message.from_user.is_bot:
        return

    voice = update.message.voice

    if voice:
        file_id = voice.file_id
        file = await context.bot.get_file(file_id)
        file_path = os.path.join(botKeyPath, f"{file.file_id}.ogg")
        await file.download_to_drive(file_path)
        print(f"Downloaded {file_path}.")

        new_file = file_path.replace("ogg", "mp3")
        audio = AudioSegment.from_ogg(file_path)
        audio.export(new_file, format="mp3")
        print(f"Changing format to mp3: {new_file}.\n")

        # fix issue with overly large files.
        chunk_files = whisper.check_file_size(new_file, save_loc)
        transcript_text = {}
        if chunk_files is not None:
            for n, cf in enumerate(chunk_files):
                transcript_text = whisper.T_or_T(cf, prompt, save_loc, save, f"transcript-{n}")

        else:
            transcript_text = whisper.T_or_T(new_file, prompt, save_loc, save, "transcript")

        await context.bot.send_message(chat_id=update.effective_chat.id, text = transcript_text["text"], reply_to_message_id=update.message.id)

        os.remove(file_path)
        os.remove(new_file)


async def translate(allow_uID: List[int], apiKeyPath, out_loc, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_uID(update, allow_uID):
        return

    # translate using original audio either
        # with state maintained (/translate -> audio) or

    # by replying to voice or audio directly.
    if update.message.reply_to_message is not None:
        audio = update.message.reply_to_message.audio
        voice = update.message.reply_to_message.voice

        if audio:
            file_id = audio.file_id
            file = await context.bot.get_file(file_id)

            file_path = os.path.join(apiKeyPath, f"{file.file_id}")

            await file.download_to_drive(file_path)

            file_audio = AudioSegment.from_file(file_path)

            print(f"Downloaded {file_path}.")

            new_file = f"{file_path}.mp3"

            file_audio.export(new_file, format="mp3")
            print(f"Changing format to mp3: {new_file}.\n")

            translated_transcript = whisper.translate(new_file, "Translate to English")
            await context.bot.send_message(chat_id=update.effective_chat.id, text = translated_transcript["text"], reply_to_message_id=update.message.id)

            os.remove(file_path)
            os.remove(new_file)

        if voice:
            file_id = voice.file_id
            file = await context.bot.get_file(file_id)

            file_path = os.path.join(apiKeyPath, f"{file.file_id}")

            await file.download_to_drive(file_path)

            file_voice = AudioSegment.from_file(file_path)

            print(f"Downloaded {file_path}.")

            new_file = f"{file_path}.mp3"

            file_voice.export(new_file, format="mp3")
            print(f"Changing format to mp3: {new_file}.\n")

            translated_transcript = whisper.translate(new_file, "Translate to English")
            await context.bot.send_message(chat_id=update.effective_chat.id, text = translated_transcript["text"], reply_to_message_id=update.message.id)

            os.remove(file_path)
            os.remove(new_file)


    else:
        print("No input audio.")
    # or detect that the transcription is not english in voice_handler and then translate the original audio.




# currently loses state with every call - i.e. no memory
# prompt vs text, does it matter?
async def gpt(allow_uID: List[int], apiKeyPath, out_loc, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_uID(update, allow_uID):
        return

    text = ""
    # /gpt as reply to another message
    if update.message.reply_to_message is not None:
        prompt_text = " ".join(context.args)
        original_message = update.message.reply_to_message
        if original_message.text is None:
            await update.message.reply_text("I cannot possibly say that!")
            return
        text = original_message.text
        if len(prompt_text) > 0:
            text = f"{prompt_text}. {text}"
    # /gpt <TYPE TEXT>
    else:
        text = " ".join(context.args)

    text = text.strip()

    if len(text) == 0:
        await update.message.reply_text(f"Even chat-GPT can't help you with the void!")
    else:
        # handle text file from transcript telegram.
        GPT_reply = call_GPT.direct_contact_GPT(text)
        the_reply = GPT_reply['choices'][0]['message']['content']
        await update.message.reply_text(the_reply)


# The goal is to have this function called every time the Bot receives a Telegram message that contains the /start command.
async def say(allow_uID: List[int], apiKeyPath, out_loc, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_uID(update, allow_uID):
        return

    text = ""

    # /say as reply to another message
    if update.message.reply_to_message is not None:
        # This is a reply to another message
        original_message = update.message.reply_to_message
        if original_message.text is None:
            await update.message.reply_text("I cannot possibly say that!")
            return
        text = original_message.text
    # /say <TYPE TEXT>
    else:
        text = " ".join(context.args)

    # await update.message.reply_text(f"I shall say {text}")
    text = text.strip()
    if len(text) == 0:
        await update.message.reply_text(f"I have nothing to say!")
    else:
        tts = elevenLabs.main(apiKeyPath, text, out_loc)
        await update.message.reply_audio(tts, title = f"{text[:20]}...", performer = "Alarak")


def main():

    #################### ARG PARSING
    parser = argparse.ArgumentParser(description='Save telegram audio.')
    parser.add_argument('-p', '--prompt', help='Prompt if desired e.g. Hello, this is a translation.', default = 'This default is used to ensure punctuation, acronyms are useful here too.')
    parser.add_argument('-b', '--botKeyPath', help='Location of bot token.')
    parser.add_argument('-o', '--out', help='Full path to save the audio clips. e.g. /mnt/usersData/whisper/')
    parser.add_argument('-s', '--save', help='string to make save file unique', default = "1")
    parser.add_argument('-a', '--apiKeyPath', help='Location of api key.')
    args = parser.parse_args()

    save = args.save
    prompt = args.prompt
    save_loc = args.out
    apiKeyPath = args.apiKeyPath
    botKeyPath = args.botKeyPath

    try:
        bot_token = read_bot_token(f"{botKeyPath}/bot_token")
    except:
        bot_token = read_bot_token()

    try:
        api_key = whisper.read_api_key(f"{apiKeyPath}/api_key")
    except:
        api_key = whisper.read_api_key()

    try:
        allowed_userID = read_allowed_uID()
    except:
        allowed_userID = []

    openai.api_key = api_key

    # Replace with your bot token
    TELEGRAM_API_TOKEN = bot_token

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    groups_filter = filters.ChatType.GROUPS

    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    start_part_func = partial(start, allowed_userID)
    start_handler = CommandHandler('start', start_part_func)

    translate_part_func = partial(translate, allowed_userID, apiKeyPath, save_loc)
    translate_handler = CommandHandler('translate', translate_part_func)

    say_part_func = partial(say, allowed_userID, apiKeyPath, save_loc)
    say_handler = CommandHandler('say', say_part_func)

    gpt_part_func = partial(gpt, allowed_userID, apiKeyPath, save_loc)
    gpt_handler = CommandHandler('gpt', gpt_part_func)

    part_func = partial(voice_handler, allowed_userID, botKeyPath, save_loc, prompt, save)
    voice_msg_handler = MessageHandler(filters.VOICE | filters.AUDIO, part_func)
    # debugged_handler = MessageHandler(None, debug_handler)

    # handle other audio file types provided
    # handle system files provided not from telegram

    application.add_handler(start_handler)
    application.add_handler(voice_msg_handler)
    # application.add_handler(debugged_handler)
    application.add_handler(say_handler)
    application.add_handler(translate_handler)
    application.add_handler(gpt_handler)


    application.run_polling()


if __name__ == '__main__':
    main()

# Great! It looks like you've successfully integrated the recent changes from the Python Telegram Bot library and adapted your code accordingly. Here's a brief overview of the changes you've made:

#     You've updated the import statements to use the new syntax for filters.
#     The start function has been updated to use the new ContextTypes type hint.
#     You've created a voice_handler function that handles voice messages. The function is called when the bot receives a voice message, and it downloads the file to the specified directory.
#     You've updated the main function to use ApplicationBuilder for creating the application object, and you've registered the start_handler and voice_msg_handler with the application.
#     Finally, you've set up argument parsing to accept the bot key path as a command-line argument.
