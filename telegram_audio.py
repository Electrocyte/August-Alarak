import logging
import os
import sys
from functools import partial
import argparse
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters



def read_bot_token(file_path: str = "bot_token") -> str:
    with open(file_path, "r") as f:
        return f.read()


# The goal is to have this function called every time the Bot receives a Telegram message that contains the /start command.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, \
                                   text="Send me a voice message and I'll send it back as an audio file!")


async def voice_handler(botKeyPath: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice

    if voice:
        file_id = voice.file_id
        file = await context.bot.get_file(file_id)
        file_path = os.path.join(botKeyPath, f"{file.file_id}.ogg")
        await file.download_to_drive(file_path)
        print(f"Downloaded {file_path}.")

        # with open(file_path, "rb") as audio_file:
        #     await context.bot.send_audio(chat_id=update.effective_chat.id, audio=InputFile(audio_file), title="Converted audio")

        # os.remove(file_path)


def main():

    #################### ARG PARSING
    parser = argparse.ArgumentParser(description='Save telegram audio.')
    parser.add_argument('-b', '--botKeyPath', help='Location of bot token.')
    args = parser.parse_args()

    botKeyPath = args.botKeyPath

    try:
        bot_token = read_bot_token()
    except:
        bot_token = read_bot_token(f"{botKeyPath}/bot_token")

    # Replace with your bot token
    TELEGRAM_API_TOKEN = bot_token

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    start_handler = CommandHandler('start', start)

    part_func = partial(voice_handler, botKeyPath)
    voice_msg_handler = MessageHandler(filters.VOICE, part_func)
    
    application.add_handler(start_handler)

    application.add_handler(voice_msg_handler)

    application.run_polling()


if __name__ == '__main__':
    main()

# Great! It looks like you've successfully integrated the recent changes from the Python Telegram Bot library and adapted your code accordingly. Here's a brief overview of the changes you've made:

#     You've updated the import statements to use the new syntax for filters.
#     The start function has been updated to use the new ContextTypes type hint.
#     You've created a voice_handler function that handles voice messages. The function is called when the bot receives a voice message, and it downloads the file to the specified directory.
#     You've updated the main function to use ApplicationBuilder for creating the application object, and you've registered the start_handler and voice_msg_handler with the application.
#     Finally, you've set up argument parsing to accept the bot key path as a command-line argument.

