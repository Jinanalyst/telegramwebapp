import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import Update, CallbackQuery

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE = "referral_system.db"

# Initialize the database
def init_db():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
                            user_id INTEGER PRIMARY KEY,
                            referred_by INTEGER,
                            referral_count INTEGER DEFAULT 0,
                            fluff_balance INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")

# Adding a user to the database
def add_user(user_id, referred_by=None):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO referrals (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")

# Update the referral count and balance when a user refers another user
def update_referral_balance(user_id):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE referrals SET referral_count = referral_count + 1, fluff_balance = fluff_balance + 10 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")

# Get the referral balance of a user
def get_referral_balance(user_id):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT referral_count, fluff_balance FROM referrals WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return None

# Generate referral link
def generate_referral_link(user_id):
    return f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"  # Replace YOUR_BOT_USERNAME with your bot's username

# Command to start the bot and send the referral link
async def start(update: Update, context):
    user_id = update.message.from_user.id
    add_user(user_id)

    referral_link = generate_referral_link(user_id)

    keyboard = [
        [InlineKeyboardButton("Go to Fluffcoin Web App", url="https://fluffcoinwebapp.opinionomics.co.kr")],
        [InlineKeyboardButton("Check Referral Balance", callback_data="check_balance")],
        [InlineKeyboardButton("Withdraw Fluffcoins", callback_data="withdraw")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = (
        f"Welcome! Here’s your referral link:\n{referral_link}\n\n"
        f"💰 **Referral Program:**\nIf you refer 1 person, you earn 10 Fluffcoins.\n\n"
        f"🏆 **Web App Task Completion:**\nComplete tasks on the web app to earn 500 Ope tokens."
    )
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Command to check referral balance
async def check_balance(update: Update, context: CallbackQuery):
    user_id = update.callback_query.from_user.id
    add_user(user_id)  # Ensure the user exists in the DB

    referral_data = get_referral_balance(user_id)

    if referral_data:
        referral_count, fluff_balance = referral_data
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(f"You have referred {referral_count} people and earned {fluff_balance} Fluffcoins.")
    else:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("No referral data found.")

# Callback to simulate Fluffcoin withdrawal
async def withdraw(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    referral_data = get_referral_balance(user_id)

    if referral_data and referral_data[1] > 0:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE referrals SET fluff_balance = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

        await query.answer()
        await query.message.reply_text(f"Withdrawal of {referral_data[1]} Fluffcoins has been requested.")
    else:
        await query.answer()
        await query.message.reply_text("You don’t have enough Fluffcoins to withdraw.")

# Handling the referral link
async def handle_referral(update: Update, context):
    user_id = update.message.from_user.id
    referred_by = None

    if update.message.text.startswith("/start"):
        start_command = update.message.text.split(" ")[1] if len(update.message.text.split(" ")) > 1 else None
        if start_command and start_command.isdigit():
            referred_by = int(start_command)

    add_user(user_id, referred_by)
    if referred_by:
        update_referral_balance(referred_by)

# Main function to set up the bot
def main():
    bot_token = os.getenv("7640518096:AAFnHfWDIp7SoVsHRr4G1nEALbdWciJBwS0")  # Fetch from environment variables

    if not bot_token:
        logger.error("Bot token is missing. Please set it as an environment variable.")
        return

    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_balance, pattern="check_balance"))
    application.add_handler(CallbackQueryHandler(withdraw, pattern="withdraw"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_referral))

    init_db()  # Initialize the database
    logger.info("Bot is starting…")
    application.run_polling()

if __name__ == '__main__':
    main()
