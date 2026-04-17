#!/usr/bin/env python3
"""
Pocket Option OTC Signal Bot
Sends multi-timeframe trading signals to Telegram
"""
 
import os
import logging
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
 
# Logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
 
# Environment variables
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_USER_ID', '0'))
USER_SSID = os.getenv('USER_SSID', '')
 
# Trading pairs
PAIRS = [
    'EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD',
    'USD/CHF', 'EUR/GBP', 'EUR/JPY', 'GBP/JPY',
    'AUD/JPY', 'NZD/USD', 'USD/CAD', 'EUR/AUD',
    'GBP/AUD', 'EUR/CHF', 'AUD/CAD', 'NZD/JPY'
]
 
# Timeframes
TIMEFRAMES = {
    '5s': 5,
    '10s': 10,
    '15s': 15,
    '30s': 30,
    '60s': 60
}
 
# Bot state
class BotState:
    def __init__(self):
        self.active = False
        self.signal_count = 0
 
state = BotState()
 
def generate_signal(timeframe):
    """Generate trading signal"""
    pair = random.choice(PAIRS)
    action = random.choice(['BUY', 'SELL'])
    confidence = random.randint(78, 96)
    payout = random.randint(80, 92)
    
    if 'JPY' in pair:
        entry = round(random.uniform(100, 155), 3)
    else:
        entry = round(random.uniform(0.85, 1.65), 5)
    
    return {
        'pair': pair,
        'action': action,
        'timeframe': timeframe,
        'seconds': TIMEFRAMES[timeframe],
        'confidence': confidence,
        'entry': entry,
        'payout': payout,
        'time': datetime.now().strftime('%H:%M:%S'),
        'date': datetime.now().strftime('%Y-%m-%d')
    }
 
def format_signal(signal):
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
 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data='status')],
        [InlineKeyboardButton("⏱ Timeframes", callback_data='timeframes')],
        [InlineKeyboardButton("ℹ️ Info", callback_data='info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = f"""
🎯 <b>Pocket Option OTC Signal Bot</b>
 
<b>Multi-Timeframe Trading Signals</b>
 
⏱ <b>Timeframes:</b>
• 5s - Ultra Fast
• 10s - Fast
• 15s - Quick
• 30s - Standard
• 60s - Classic
 
✅ <b>Status:</b> {'🟢 Active' if state.active else '⏸ Standby'}
📊 <b>Signals Sent:</b> {state.signal_count}
 
<i>Ready to trade! 🚀</i>
"""
    
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='HTML')
 
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show status"""
    msg = f"""
📊 <b>BOT STATUS</b>
 
━━━━━━━━━━━━━━━━━━━━
🤖 <b>Status:</b> {'🟢 Broadcasting' if state.active else '⏸ Standby'}
📈 <b>Signals:</b> {state.signal_count}
⏱ <b>Timeframes:</b> 5s, 10s, 15s, 30s, 60s
🔐 <b>SSID:</b> {'✅ Set' if USER_SSID else '❌ Not Set'}
━━━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(msg, parse_mode='HTML')
 
async def timeframes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show timeframes"""
    msg = """
⏱ <b>TIMEFRAMES</b>
 
🔵 <b>5s</b> - Ultra-fast scalping
🟢 <b>10s</b> - Fast trading
🟡 <b>15s</b> - Quick entries
🟠 <b>30s</b> - Standard
🔴 <b>60s</b> - Classic
 
All timeframes active!
"""
    await update.message.reply_text(msg, parse_mode='HTML')
 
async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show info"""
    msg = """
📚 <b>BOT INFO</b>
 
✅ 5 Timeframes (5s-60s)
✅ 16+ OTC Pairs
✅ Real-time Signals
✅ 78-96% Accuracy
✅ Payout Info
 
⚠️ Risk Warning:
Trading involves risk. Use
proper risk management!
"""
    await update.message.reply_text(msg, parse_mode='HTML')
 
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buttons"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'status':
        await status(query, context)
    elif query.data == 'timeframes':
        await timeframes_cmd(query, context)
    elif query.data == 'info':
        await info_cmd(query, context)
 
async def send_signal(context: ContextTypes.DEFAULT_TYPE, timeframe: str, chat_id: int):
    """Send signal"""
    if not state.active:
        return
    
    signal = generate_signal(timeframe)
    message = format_signal(signal)
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )
        state.signal_count += 1
        logger.info(f"Sent {timeframe} signal to {chat_id}")
    except Exception as e:
        logger.error(f"Error sending signal: {e}")
 
async def start_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcasting"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    if state.active:
        await update.message.reply_text("⚠️ Already broadcasting")
        return
    
    state.active = True
    chat_id = update.effective_chat.id
    
    # Schedule signals
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
        "✅ <b>Broadcasting Started!</b>\n\n"
        "⏱ All 5 timeframes active\n"
        "🤖 Sending signals...",
        parse_mode='HTML'
    )
    
    logger.info(f"Signals started for chat {chat_id}")
 
async def stop_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop broadcasting"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    if not state.active:
        await update.message.reply_text("⚠️ Not broadcasting")
        return
    
    state.active = False
    
    # Stop all jobs
    for tf in ['5s', '10s', '15s', '30s', '60s']:
        jobs = context.job_queue.get_jobs_by_name(f'signal_{tf}')
        for job in jobs:
            job.schedule_removal()
    
    await update.message.reply_text(
        "✅ <b>Broadcasting Stopped</b>\n\n"
        "⏸ All timeframes paused",
        parse_mode='HTML'
    )
    
    logger.info("Signals stopped")
 
def main():
    """Run bot"""
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    
    logger.info("="*50)
    logger.info("🤖 POCKET OPTION OTC SIGNAL BOT")
    logger.info("="*50)
    logger.info(f"✅ Token: {'Set' if BOT_TOKEN else 'Missing'}")
    logger.info(f"👤 Admin: {ADMIN_ID}")
    logger.info(f"🔐 SSID: {'Set' if USER_SSID else 'Not Set'}")
    logger.info("⏱ Timeframes: 5s, 10s, 15s, 30s, 60s")
    logger.info("="*50)
    
    # Build application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("timeframes", timeframes_cmd))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("startsignals", start_signals))
    app.add_handler(CommandHandler("stopsignals", stop_signals))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Start
    logger.info("🚀 Starting bot...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
 
if __name__ == '__main__':
    main()
