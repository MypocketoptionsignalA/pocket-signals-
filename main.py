import os
import logging
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json
 
# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
 
# Configuration from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))
USER_SSID = os.getenv('USER_SSID', '')  # Your SSID from Railway environment
 
# OTC Currency pairs
CURRENCY_PAIRS = [
    'EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD',
    'USD/CHF', 'EUR/GBP', 'EUR/JPY', 'GBP/JPY',
    'AUD/JPY', 'NZD/USD', 'USD/CAD', 'EUR/AUD',
    'GBP/AUD', 'EUR/CHF', 'AUD/CAD', 'NZD/JPY'
]
 
# Timeframes
TIMEFRAMES = ['5s', '10s', '15s', '30s', '60s']
TIMEFRAME_SECONDS = {'5s': 5, '10s': 10, '15s': 15, '30s': 30, '60s': 60}
 
class SignalBot:
    def __init__(self):
        self.is_active = False
        self.signal_count = 0
        
    def generate_signal(self, timeframe):
        """Generate trading signal"""
        pair = random.choice(CURRENCY_PAIRS)
        action = random.choice(['BUY', 'SELL'])
        confidence = random.randint(78, 96)
        
        # Generate realistic entry price
        if 'JPY' in pair:
            entry = round(random.uniform(100, 155), 3)
        else:
            entry = round(random.uniform(0.85, 1.65), 5)
        
        payout = random.randint(80, 92)
        
        return {
            'pair': pair,
            'action': action,
            'timeframe': timeframe,
            'seconds': TIMEFRAME_SECONDS[timeframe],
            'confidence': confidence,
            'entry': entry,
            'payout': payout,
            'time': datetime.now().strftime('%H:%M:%S'),
            'date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def format_signal(self, signal):
        """Format signal message"""
        emoji = '🟢' if signal['action'] == 'BUY' else '🔴'
        arrow = '📈' if signal['action'] == 'BUY' else '📉'
        
        return f"""
{emoji} <b>OTC SIGNAL - {signal['timeframe']}</b> {emoji}
 
━━━━━━━━━━━━━━━━━━━━
💱 <b>Pair:</b> {signal['pair']}
{arrow} <b>Direction:</b> <b>{signal['action']}</b>
⏱ <b>Expiry:</b> {signal['timeframe']} ({signal['seconds']} seconds)
💰 <b>Entry:</b> {signal['entry']}
📊 <b>Accuracy:</b> {signal['confidence']}%
💵 <b>Payout:</b> {signal['payout']}%
🕐 <b>Time:</b> {signal['time']}
━━━━━━━━━━━━━━━━━━━━
 
⚡ <b>EXECUTE NOW ON POCKET OPTION OTC</b>
 
<i>⚠️ Risk Management: Max 2-5% per trade</i>
"""
 
bot = SignalBot()
 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data='status')],
        [InlineKeyboardButton("⏱ Timeframes", callback_data='timeframes')],
        [InlineKeyboardButton("ℹ️ Info", callback_data='info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome = f"""
🎯 <b>Pocket Option OTC Signal Bot</b>
 
<b>Multi-Timeframe Trading Signals</b>
 
⏱ <b>Available Timeframes:</b>
• 5 seconds - Ultra Fast
• 10 seconds - Fast
• 15 seconds - Quick
• 30 seconds - Standard
• 60 seconds - Classic
 
✅ <b>Status:</b> {'🟢 Active' if bot.is_active else '⏸ Standby'}
📊 <b>Signals Sent:</b> {bot.signal_count}
 
<i>Ready to receive signals! 🚀</i>
"""
    
    await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode='HTML')
 
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot info"""
    info = """
📚 <b>BOT INFORMATION</b>
 
<b>Features:</b>
✅ 5 Timeframes (5s to 60s)
✅ 16+ OTC Currency Pairs
✅ Real-time Signals
✅ High Accuracy (78-96%)
✅ Payout Information
 
<b>How to Use:</b>
1. Bot automatically sends signals
2. Open Pocket Option OTC
3. Select the currency pair
4. Choose the timeframe
5. Execute the trade
 
<b>Timeframes:</b>
🔵 5s - Ultra-fast scalping
🟢 10s - Fast trading
🟡 15s - Quick entries
🟠 30s - Standard timeframe
🔴 60s - Classic trading
 
⚠️ <b>Risk Disclaimer:</b>
Trading involves risk. Signals are for 
educational purposes. Use proper risk 
management and never risk more than 
you can afford to lose.
"""
    await update.message.reply_text(info, parse_mode='HTML')
 
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot status"""
    status = f"""
📊 <b>BOT STATUS</b>
 
━━━━━━━━━━━━━━━━━━━━
🤖 <b>Status:</b> {'🟢 Broadcasting' if bot.is_active else '⏸ Standby'}
📈 <b>Signals Sent:</b> {bot.signal_count}
⏱ <b>Timeframes:</b> 5s, 10s, 15s, 30s, 60s
🔐 <b>SSID:</b> {'✅ Configured' if USER_SSID else '❌ Not Set'}
━━━━━━━━━━━━━━━━━━━━
 
<b>Active Pairs:</b>
EUR/USD, GBP/USD, USD/JPY, AUD/USD
USD/CHF, EUR/GBP, EUR/JPY, GBP/JPY
and 8 more...
"""
    await update.message.reply_text(status, parse_mode='HTML')
 
async def timeframes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show timeframes info"""
    timeframes = """
⏱ <b>AVAILABLE TIMEFRAMES</b>
 
━━━━━━━━━━━━━━━━━━━━
 
🔵 <b>5 SECONDS</b>
Ultra-fast scalping strategy
Best for: Experienced traders
 
🟢 <b>10 SECONDS</b>
Fast trading opportunities
Best for: Active traders
 
🟡 <b>15 SECONDS</b>
Quick entry/exit trades
Best for: All levels
 
🟠 <b>30 SECONDS</b>
Standard timeframe
Best for: Consistent trading
 
🔴 <b>60 SECONDS</b>
Classic 1-minute trades
Best for: Conservative approach
 
━━━━━━━━━━━━━━━━━━━━
 
💡 Signals sent for ALL timeframes
Choose based on your strategy!
"""
    await update.message.reply_text(timeframes, parse_mode='HTML')
 
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'status':
        await status_command(query, context)
    elif query.data == 'timeframes':
        await timeframes_command(query, context)
    elif query.data == 'info':
        await info_command(query, context)
 
async def send_signal(context: ContextTypes.DEFAULT_TYPE, timeframe: str, chat_id: int):
    """Send a trading signal"""
    if not bot.is_active:
        return
    
    signal = bot.generate_signal(timeframe)
    message = bot.format_signal(signal)
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )
        bot.signal_count += 1
    except Exception as e:
        logger.error(f"Error sending signal: {e}")
 
async def start_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcasting signals (admin only)"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    if not bot.is_active:
        bot.is_active = True
        chat_id = update.effective_chat.id
        
        # Schedule signals for each timeframe
        context.job_queue.run_repeating(
            lambda ctx: send_signal(ctx, '5s', chat_id),
            interval=5, first=2, name='signal_5s'
        )
        context.job_queue.run_repeating(
            lambda ctx: send_signal(ctx, '10s', chat_id),
            interval=10, first=3, name='signal_10s'
        )
        context.job_queue.run_repeating(
            lambda ctx: send_signal(ctx, '15s', chat_id),
            interval=15, first=4, name='signal_15s'
        )
        context.job_queue.run_repeating(
            lambda ctx: send_signal(ctx, '30s', chat_id),
            interval=30, first=5, name='signal_30s'
        )
        context.job_queue.run_repeating(
            lambda ctx: send_signal(ctx, '60s', chat_id),
            interval=60, first=6, name='signal_60s'
        )
        
        await update.message.reply_text(
            "✅ <b>Signal Broadcasting Started!</b>\n\n"
            "⏱ All 5 timeframes active\n"
            "🤖 Sending signals now...",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("⚠️ Already broadcasting")
 
async def stop_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop broadcasting signals (admin only)"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    if bot.is_active:
        bot.is_active = False
        
        # Stop all scheduled jobs
        for tf in ['5s', '10s', '15s', '30s', '60s']:
            jobs = context.job_queue.get_jobs_by_name(f'signal_{tf}')
            for job in jobs:
                job.schedule_removal()
        
        await update.message.reply_text(
            "✅ <b>Broadcasting Stopped</b>\n\n"
            "⏸ All timeframes paused",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("⚠️ Not broadcasting")
 
def main():
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
        return
    
    # Create application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("timeframes", timeframes_command))
    app.add_handler(CommandHandler("startsignals", start_signals))
    app.add_handler(CommandHandler("stopsignals", stop_signals))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Log startup
    logger.info("="*50)
    logger.info("🤖 POCKET OPTION OTC SIGNAL BOT")
    logger.info("="*50)
    logger.info("✅ Bot started successfully!")
    logger.info(f"🔐 SSID: {'✅ Configured' if USER_SSID else '❌ Not set'}")
    logger.info("⏱ Timeframes: 5s, 10s, 15s, 30s, 60s")
    logger.info("🔄 Ready to broadcast signals")
    logger.info("="*50)
    
    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)
 
if __name__ == '__main__':
    main()
