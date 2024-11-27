import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import Bot

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE = "referral_system.db"

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
                        user_id INTEGER PRIMARY KEY,
                        referred_by INTEGER,
                        referral_count INTEGER DEFAULT 0,
                        fluff_balance INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# Adding a user to the database
def add_user(user_id, referred_by=None):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO referrals (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
    conn.commit()
    conn.close()

# Update the referral count and balance when a user refers another user
def update_referral_balance(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE referrals SET referral_count = referral_count + 1, fluff_balance = fluff_balance + 10 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Get the referral balance of a user
def get_referral_balance(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT referral_count, fluff_balance FROM referrals WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

# Generate referral link
def generate_referral_link(user_id):
    return f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"

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

    # Log to check if the keyboard is being created
    logger.info("Sending welcome message with inline keyboard")

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
# Command to check referral balance
async def check_balance(update: Update, context: CallbackQuery):
    user_id = update.callback_query.from_user.id
    add_user(user_id)  # Ensure the user exists in the DB

    referral_data = get_referral_balance(user_id)
    if referral_data:
        referral_count, fluff_balance = referral_data
        await update.callback_query.answer(f"You have referred {referral_count} people and earned {fluff_balance} Fluffcoins.")
    else:
        await update.callback_query.answer("No referral data found.")

# Command to simulate Fluffcoin withdrawal
async def withdraw(update: Update, context: CallbackQuery):
    user_id = update.callback_query.from_user.id
    add_user(user_id)  # Ensure the user exists in the DB

    referral_data = get_referral_balance(user_id)
    if referral_data and referral_data[1] > 0:
        await update.callback_query.answer(f"Withdrawal of {referral_data[1]} Fluffcoins has been requested.")
        # Reset the fluff_balance after withdrawal
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE referrals SET fluff_balance = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
    else:
        await update.callback_query.answer("You don’t have enough Fluffcoins to withdraw.")

# Handling the referral link
async def handle_referral(update: Update, context):
    user_id = update.message.from_user.id
    referred_by = None
    if update.message.text.startswith("/start"):
        # Extract referral user ID from the /start command
        start_command = update.message.text.split(" ")[1] if len(update.message.text.split(" ")) > 1 else None
        if start_command and start_command.isdigit():
            referred_by = int(start_command)

    # Add the user and associate them with a referrer if present
    add_user(user_id, referred_by)
    if referred_by:
        update_referral_balance(referred_by)  # Reward the referrer

# Main function to set up the bot
def main():
    # Replace with your bot token
    bot_token = "7640518096:AAFnHfWDIp7SoVsHRr4G1nEALbdWciJBwS0"
    bot_token = os.getenv("7640518096:AAFnHfWDIp7SoVsHRr4G1nEALbdWciJBwS0")

    # Create the Application and pass it your bot's token
    application = Application.builder().token(bot_token).build()

    # Add a command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Add command handlers for referral balance and withdrawal
    application.add_handler(CallbackQueryHandler(check_balance, pattern="check_balance"))
    application.add_handler(CallbackQueryHandler(withdraw, pattern="withdraw"))

    # Add message handler for referral
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_referral))

    # Run the bot until you send a signal to stop
    application.run_polling()

if __name__ == '__main__':
    init_db()  # Initialize the database
    main()
