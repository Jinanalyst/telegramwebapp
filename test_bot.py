from telegram import Update
from telegram.ext import Application, CommandHandler
import logging

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Command handler for /start
async def start(update: Update, context):
    await update.message.reply_text("Hello from the bot!")

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Add a command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Run the bot until you send a signal to stop
    application.run_polling()

if __name__ == '__main__':
    main()