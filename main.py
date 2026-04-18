import os
import logging
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_USER_ID', '0'))
 
PAIRS = ['GBP/USD OTC', 'USD/JPY OTC', 'EUR/USD OTC', 'AUD/USD OTC', 'GBP/JPY OTC', 'EUR/JPY OTC']
TIMEFRAMES = {'5s': 5, '10s': 10, '15s': 15, '30s': 30, '60s': 60}
 
class State:
    active = False
    count = 0
 
state = State()
 
def gen_signal(tf):
    pair = random.choice(PAIRS)
    action = random.choice(['BUY', 'SELL'])
    
    # Stylish emoji format like screenshot
    if action == 'BUY':
        emoji = '🚀'
        arrow = '📈'
    else:
        emoji = '🚨'
        arrow = '📉'
    
    return f"""
📊 <b>{action} SIGNAL! {emoji}</b>
{arrow} <b>{pair}</b>
⚡️ <b>Enter NOW 🔥</b>
 
⏰ Expiry: <b>{tf}</b>
🎯 Action: <b>{action}</b>
🕐 Time: <b>{datetime.now().strftime('%I:%M %p')}</b>
"""
 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📊 Status", callback_data='status')],
        [InlineKeyboardButton("🚀 Start Signals", callback_data='start_sig')]
    ]
    msg = f"""
🎯 <b>Pocket Option Signal Bot</b>
 
⏱ <b>Timeframes:</b> 5s, 10s, 15s, 30s, 60s
 
✅ <b>Status:</b> {'🟢 Active' if state.active else '⏸ Standby'}
📊 <b>Signals:</b> {state.count}
 
<i>Tap "Start Signals" to begin! 🚀</i>
"""
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')
 
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"""
📊 <b>STATUS</b>
 
🤖 {'🟢 Broadcasting' if state.active else '⏸ Standby'}
📈 Signals: {state.count}
⏱ Timeframes: 5s, 10s, 15s, 30s, 60s
"""
    await update.message.reply_text(msg, parse_mode='HTML')
 
async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'status':
        await status(query, context)
    elif query.data == 'start_sig':
        # Simulate /startsignals
        if not state.active:
            state.active = True
            cid = query.message.chat_id
            
            context.job_queue.run_repeating(lambda c: send_sig(c, '5s', cid), interval=5, first=2, name='s5')
            context.job_queue.run_repeating(lambda c: send_sig(c, '10s', cid), interval=10, first=3, name='s10')
            context.job_queue.run_repeating(lambda c: send_sig(c, '15s', cid), interval=15, first=4, name='s15')
            context.job_queue.run_repeating(lambda c: send_sig(c, '30s', cid), interval=30, first=5, name='s30')
            context.job_queue.run_repeating(lambda c: send_sig(c, '60s', cid), interval=60, first=6, name='s60')
            
            await query.edit_message_text("✅ <b>Signals Started! 🚀</b>\n\n⏱ All timeframes active\n📊 Watch for signals!", parse_mode='HTML')
        else:
            await query.edit_message_text("⚠️ Already active!")
 
async def send_sig(context: ContextTypes.DEFAULT_TYPE, tf: str, cid: int):
    if not state.active:
        return
    try:
        await context.bot.send_message(chat_id=cid, text=gen_signal(tf), parse_mode='HTML')
        state.count += 1
    except Exception as e:
        logger.error(f"Error: {e}")
 
async def start_sig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    if state.active:
        await update.message.reply_text("⚠️ Already active")
        return
    
    state.active = True
    cid = update.effective_chat.id
    
    context.job_queue.run_repeating(lambda c: send_sig(c, '5s', cid), interval=5, first=2, name='s5')
    context.job_queue.run_repeating(lambda c: send_sig(c, '10s', cid), interval=10, first=3, name='s10')
    context.job_queue.run_repeating(lambda c: send_sig(c, '15s', cid), interval=15, first=4, name='s15')
    context.job_queue.run_repeating(lambda c: send_sig(c, '30s', cid), interval=30, first=5, name='s30')
    context.job_queue.run_repeating(lambda c: send_sig(c, '60s', cid), interval=60, first=6, name='s60')
    
    await update.message.reply_text("✅ <b>Signals Started! 🚀</b>\n\n⏱ All timeframes active", parse_mode='HTML')
 
async def stop_sig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    if not state.active:
        await update.message.reply_text("⚠️ Not active")
        return
    
    state.active = False
    for name in ['s5', 's10', 's15', 's30', 's60']:
        for job in context.job_queue.get_jobs_by_name(name):
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
    app.add_handler(CommandHandler("startsignals", start_sig))
    app.add_handler(CommandHandler("stopsignals", stop_sig))
    app.add_handler(CallbackQueryHandler(btn))
    
    logger.info("🚀 Bot running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
 
if __name__ == '__main__':
    main()
