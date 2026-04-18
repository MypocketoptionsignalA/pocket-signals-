import os
import logging
import random
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_USER_ID', '0'))
 
# South Africa timezone
SA_TZ = pytz.timezone('Africa/Johannesburg')
 
# OTC Pairs - exactly like Aether IQ
OTC_PAIRS = [
    'AUD/CHF OTC', 'GBP/JPY OTC', 'QAR/CNY OTC',
    'CAD/JPY OTC', 'AED/CNY OTC', 'EUR/USD OTC',
    'BHD/CNY OTC', 'EUR/GBP OTC', 'NZD/USD OTC',
    'LBP/USD OTC', 'NGN/USD OTC', 'AUD/USD OTC',
    'GBP/AUD OTC', 'USD/JPY OTC', 'EUR/JPY OTC'
]
 
# Timeframes
TIMEFRAMES = {
    '5 Seconds': 5,
    '10 Seconds': 10,
    '15 Seconds': 15,
    '30 Seconds': 30,
    '60 Seconds': 60
}
 
class State:
    active = False
    count = 0
    selected_pair = None
    selected_timeframe = None
 
state = State()
 
def gen_signal(pair, action):
    emoji = '🚀' if action == 'BUY' else '🚨'
    arrow = '📈' if action == 'BUY' else '📉'
    
    # Get South Africa time
    sa_time = datetime.now(SA_TZ).strftime('%I:%M %p')
    
    return f"""
📊 <b>{action} SIGNAL! {emoji}</b>
{arrow} <b>{pair}</b>
⚡️ <b>Enter NOW 🔥</b>
 
🎯 Action: <b>{action}</b>
🕐 Time: <b>{sa_time} SAST</b>
🌍 Timezone: <b>South Africa</b>
"""
 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Stop any active signals first
    if state.active:
        state.active = False
        cid = update.effective_chat.id
        current_jobs = context.job_queue.get_jobs_by_name(f'signal_{cid}')
        for job in current_jobs:
            job.schedule_removal()
    
    # Reset state
    state.selected_pair = None
    state.selected_timeframe = None
    
    msg = "🎯 <b>Select an OTC pair:</b>"
    
    # Create keyboard with OTC pairs (3 per row like Aether IQ)
    keyboard = []
    for i in range(0, len(OTC_PAIRS), 3):
        row = [
            InlineKeyboardButton(OTC_PAIRS[j], callback_data=f'pair_{OTC_PAIRS[j]}')
            for j in range(i, min(i + 3, len(OTC_PAIRS)))
        ]
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='HTML')
 
async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Handle pair selection
    if data.startswith('pair_'):
        pair = data.replace('pair_', '')
        state.selected_pair = pair
        
        # Show timeframe selection
        msg = f"<b>Please Choose Time to Trade for {pair}</b>"
        
        keyboard = [
            [
                InlineKeyboardButton("5 Seconds", callback_data='time_5 Seconds'),
                InlineKeyboardButton("10 Seconds", callback_data='time_10 Seconds'),
                InlineKeyboardButton("15 Seconds", callback_data='time_15 Seconds')
            ],
            [
                InlineKeyboardButton("30 Seconds", callback_data='time_30 Seconds'),
                InlineKeyboardButton("60 Seconds", callback_data='time_60 Seconds')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode='HTML')
    
    # Handle timeframe selection
    elif data.startswith('time_'):
        timeframe = data.replace('time_', '')
        state.selected_timeframe = timeframe
        
        # Stop any existing signals
        cid = query.message.chat_id
        current_jobs = context.job_queue.get_jobs_by_name(f'signal_{cid}')
        for job in current_jobs:
            job.schedule_removal()
        
        # Start fresh signals
        state.active = True
        
        # Send signals for selected timeframe
        interval = TIMEFRAMES[timeframe]
        context.job_queue.run_repeating(
            lambda c: send_selected_signal(c, cid),
            interval=interval,
            first=2,
            name=f'signal_{cid}'
        )
        
        await query.edit_message_text(
            f"✅ <b>Signals Started! 🚀</b>\n\n"
            f"📊 Pair: {state.selected_pair}\n"
            f"⏱ Timeframe: {timeframe}\n\n"
            f"📈 Watch for signals!",
            parse_mode='HTML'
        )
 
async def send_selected_signal(context: ContextTypes.DEFAULT_TYPE, cid: int):
    if not state.active or not state.selected_pair:
        logger.warning(f"Not sending signal - active: {state.active}, pair: {state.selected_pair}")
        return
    
    action = random.choice(['BUY', 'SELL'])
    signal = gen_signal(state.selected_pair, action)
    
    try:
        await context.bot.send_message(chat_id=cid, text=signal, parse_mode='HTML')
        state.count += 1
        logger.info(f"✅ Signal sent! Count: {state.count} | Pair: {state.selected_pair} | Action: {action}")
    except Exception as e:
        logger.error(f"❌ Error sending signal: {e}")
 
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"""
📊 <b>STATUS</b>
 
🤖 {'🟢 Broadcasting' if state.active else '⏸ Standby'}
📈 Signals: {state.count}
💱 Pair: {state.selected_pair if state.selected_pair else 'Not selected'}
⏱ Timeframe: {state.selected_timeframe if state.selected_timeframe else 'Not selected'}
"""
    await update.message.reply_text(msg, parse_mode='HTML')
 
async def stop_sig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state.active:
        await update.message.reply_text("⚠️ Not active")
        return
    
    state.active = False
    
    # Remove all signal jobs
    current_jobs = context.job_queue.get_jobs_by_name(f'signal_{update.effective_chat.id}')
    for job in current_jobs:
        job.schedule_removal()
    
    await update.message.reply_text("✅ <b>Stopped</b>", parse_mode='HTML')
 
def main():
    if not BOT_TOKEN:
        logger.error("❌ No token!")
        return
    
    logger.info("🤖 Starting Pocket Option Signal Bot...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stop", stop_sig))
    app.add_handler(CallbackQueryHandler(btn))
    
    logger.info("🚀 Bot running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
 
if __name__ == '__main__':
    main()
