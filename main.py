import os
import logging
import random
from datetime import datetime
import pytz
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_USER_ID', '0'))
 
# South Africa timezone
SA_TZ = pytz.timezone('Africa/Johannesburg')
 
# OTC Pairs
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
 
def create_signal_image(action):
    """Create BUY or SELL visual image"""
    # Create 800x600 image with black background
    img = Image.new('RGB', (800, 600), color='black')
    draw = ImageDraw.Draw(img)
    
    if action == 'BUY':
        # BUY - Gradient blue to purple with UP arrow
        color1 = (0, 200, 255)  # Cyan
        color2 = (200, 0, 255)  # Purple
        arrow_points = [(300, 450), (500, 450), (400, 150)]  # UP triangle
    else:
        # SELL - Gradient red to orange with DOWN arrow
        color1 = (255, 50, 50)  # Red
        color2 = (255, 150, 0)  # Orange
        arrow_points = [(300, 150), (500, 150), (400, 450)]  # DOWN triangle
    
    # Draw gradient background
    for y in range(600):
        r = int(color1[0] + (color2[0] - color1[0]) * y / 600)
        g = int(color1[1] + (color2[1] - color1[1]) * y / 600)
        b = int(color1[2] + (color2[2] - color1[2]) * y / 600)
        draw.rectangle([(0, y), (800, y+1)], fill=(r, g, b))
    
    # Draw arrow triangle
    draw.polygon(arrow_points, outline='white', width=10)
    
    # Draw BUY or SELL text (large)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 180)
    except:
        font = ImageFont.load_default()
    
    # Center the text
    text = action
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((800 - text_width) // 2, 450)
    
    # Draw text with glow effect
    for offset in [(2,2), (-2,-2), (2,-2), (-2,2)]:
        draw.text((position[0]+offset[0], position[1]+offset[1]), text, fill='black', font=font)
    draw.text(position, text, fill='white', font=font)
    
    return img
 
def gen_caption(pair, action, timeframe):
    """Generate caption for signal"""
    sa_time = datetime.now(SA_TZ).strftime('%I:%M %p')
    emoji = '🚀' if action == 'BUY' else '🚨'
    
    return f"""
{emoji} <b>{action} SIGNAL!</b>
 
📊 <b>Pair:</b> {pair}
⏱ <b>Timeframe:</b> {timeframe}
🕐 <b>Time:</b> {sa_time} SAST
 
⚡️ <b>ENTER NOW!</b> 🔥
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
    
    # Create keyboard with OTC pairs (3 per row)
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
            f"📈 Watch for visual signals!",
            parse_mode='HTML'
        )
 
async def send_selected_signal(context: ContextTypes.DEFAULT_TYPE, cid: int):
    if not state.active or not state.selected_pair:
        logger.warning(f"Not sending signal - active: {state.active}, pair: {state.selected_pair}")
        return
    
    action = random.choice(['BUY', 'SELL'])
    
    try:
        # Create signal image
        img = create_signal_image(action)
        
        # Save to BytesIO
        bio = BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)
        
        # Generate caption
        caption = gen_caption(state.selected_pair, action, state.selected_timeframe)
        
        # Send photo with caption
        await context.bot.send_photo(
            chat_id=cid,
            photo=bio,
            caption=caption,
            parse_mode='HTML'
        )
        
        state.count += 1
        logger.info(f"✅ Visual signal sent! Count: {state.count} | Pair: {state.selected_pair} | Action: {action}")
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
    
    logger.info("🤖 Starting Pocket Option Visual Signal Bot...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stop", stop_sig))
    app.add_handler(CallbackQueryHandler(btn))
    
    logger.info("🚀 Bot running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
 
if __name__ == '__main__':
    main()
