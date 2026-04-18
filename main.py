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
 
# Extended OTC Pairs (30+ pairs)
OTC_PAIRS = [
    'GBP/USD OTC', 'USD/JPY OTC', 'EUR/USD OTC', 'AUD/USD OTC',
    'GBP/JPY OTC', 'EUR/JPY OTC', 'AUD/JPY OTC', 'NZD/USD OTC',
    'USD/CHF OTC', 'EUR/GBP OTC', 'GBP/AUD OTC', 'EUR/AUD OTC',
    'AUD/CHF OTC', 'CAD/JPY OTC', 'QAR/CNY OTC', 'AED/CNY OTC',
    'BHD/CNY OTC', 'EUR/CHF OTC', 'NZD/JPY OTC', 'LBP/USD OTC',
    'NGN/USD OTC', 'GBP/CHF OTC', 'AUD/NZD OTC', 'EUR/CAD OTC',
    'GBP/CAD OTC', 'USD/CAD OTC', 'CHF/JPY OTC', 'NZD/CAD OTC',
    'CAD/CHF OTC', 'EUR/NZD OTC'
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
    def __init__(self):
        self.active = {}
        self.count = {}
        self.selected_pair = {}
        self.selected_timeframe = {}
 
state = State()
 
def gen_signal(pair, action):
    """Generate signal text"""
    sa_time = datetime.now(SA_TZ).strftime('%I:%M %p')
    
    if action == 'BUY':
        emoji = '🚀'
    else:
        emoji = '🚨'
    
    return f"""📊 <b>{action} SIGNAL! {emoji}</b>
<b>Enter NOW 🔥</b>
 
💱 <b>Pair:</b> {pair}
🕐 <b>Time:</b> {sa_time}"""
 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"🎬 START command from user {user_id}")
    
    # Stop any active signals
    if state.active.get(user_id, False):
        state.active[user_id] = False
        current_jobs = context.job_queue.get_jobs_by_name(f'signal_{user_id}')
        for job in current_jobs:
            job.schedule_removal()
    
    # Reset state
    state.selected_pair[user_id] = None
    state.selected_timeframe[user_id] = None
    
    msg = "🎯 <b>Select an OTC pair:</b>"
    
    # Create keyboard
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
    
    user_id = query.from_user.id
    data = query.data
    
    logger.info(f"🔘 Button: {data} from user {user_id}")
    
    # Handle pair selection
    if data.startswith('pair_'):
        pair = data.replace('pair_', '')
        state.selected_pair[user_id] = pair
        logger.info(f"✅ Pair selected: {pair}")
        
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
        state.selected_timeframe[user_id] = timeframe
        logger.info(f"⏱ Timeframe selected: {timeframe}")
        
        # Stop old jobs
        cid = query.message.chat_id
        current_jobs = context.job_queue.get_jobs_by_name(f'signal_{user_id}')
        for job in current_jobs:
            job.schedule_removal()
        
        # Initialize
        if user_id not in state.count:
            state.count[user_id] = 0
        
        state.active[user_id] = True
        pair = state.selected_pair[user_id]
        interval = TIMEFRAMES[timeframe]
        
        logger.info(f"🟢 ACTIVE! User {user_id}, Pair: {pair}, Interval: {interval}s")
        
        # Show activation message
        await query.edit_message_text(
            f"✅ <b>SIGNALS ACTIVATED!</b>\n\n"
            f"📊 Pair: {pair}\n"
            f"⏱ Timeframe: {timeframe}\n\n"
            f"🚀 First signal in 3 seconds...",
            parse_mode='HTML'
        )
        
        # Schedule first signal
        logger.info(f"📅 Scheduling first signal in 3 seconds...")
        context.job_queue.run_once(
            lambda c: send_signal(c, cid, user_id),
            when=3,
            name=f'first_{user_id}'
        )
        
        # Schedule recurring signals
        logger.info(f"📅 Scheduling recurring signals every {interval}s...")
        context.job_queue.run_repeating(
            lambda c: send_signal(c, cid, user_id),
            interval=interval,
            first=interval + 3,
            name=f'signal_{user_id}'
        )
        
        logger.info(f"✅✅✅ ALL SIGNALS SCHEDULED!")
 
async def send_signal(context: ContextTypes.DEFAULT_TYPE, cid: int, user_id: int):
    """Send a signal"""
    logger.info(f"🎯 send_signal called for user {user_id}")
    
    if not state.active.get(user_id, False):
        logger.warning(f"⚠️ Not active for user {user_id}")
        return
    
    pair = state.selected_pair.get(user_id)
    if not pair:
        logger.warning(f"⚠️ No pair for user {user_id}")
        return
    
    action = random.choice(['BUY', 'SELL'])
    signal_text = gen_signal(pair, action)
    
    try:
        await context.bot.send_message(chat_id=cid, text=signal_text, parse_mode='HTML')
        state.count[user_id] = state.count.get(user_id, 0) + 1
        logger.info(f"✅✅✅ SIGNAL SENT! User {user_id} | {action} | {pair} | Count: {state.count[user_id]}")
    except Exception as e:
        logger.error(f"❌ Error sending signal: {e}")
 
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    msg = f"""📊 <b>STATUS</b>
 
🤖 {'🟢 Broadcasting' if state.active.get(user_id, False) else '⏸ Standby'}
📈 Signals: {state.count.get(user_id, 0)}
💱 Pair: {state.selected_pair.get(user_id, 'Not selected')}
⏱ Timeframe: {state.selected_timeframe.get(user_id, 'Not selected')}"""
    
    await update.message.reply_text(msg, parse_mode='HTML')
 
async def stop_sig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not state.active.get(user_id, False):
        await update.message.reply_text("⚠️ Not active")
        return
    
    state.active[user_id] = False
    
    # Remove jobs
    current_jobs = context.job_queue.get_jobs_by_name(f'signal_{user_id}')
    for job in current_jobs:
        job.schedule_removal()
    
    await update.message.reply_text("✅ <b>Stopped</b>", parse_mode='HTML')
    logger.info(f"🛑 Stopped for user {user_id}")
 
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
    
    logger.info("🚀 Bot running with 30+ OTC pairs!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
 
if __name__ == '__main__':
    main()
 
