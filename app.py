import os
import asyncio
import logging
import time
from pathlib import Path
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "666727062"))

STORAGE_DIR = Path("/tmp/media_bot")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📖 راهنما"), KeyboardButton(text="🎧 پشتیبانی")]],
    resize_keyboard=True
)

def get_media_keyboard(filename: str, is_video: bool = True):
    if is_video:
        buttons = [
            [InlineKeyboardButton(text="✂ برش", callback_data=f"trim:{filename}"),
             InlineKeyboardButton(text="🎵 MP3", callback_data=f"mp3:{filename}")],
            [InlineKeyboardButton(text="📐 720p", callback_data=f"q:720:{filename}"),
             InlineKeyboardButton(text="📐 480p", callback_data=f"q:480:{filename}"),
             InlineKeyboardButton(text="📐 360p", callback_data=f"q:360:{filename}")]
        ]
    else:
        buttons = [[InlineKeyboardButton(text="✂ برش", callback_data=f"trim:{filename}")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def download_media(url: str, output_path: str):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'noplaylist': True,
        'quiet': True,
    }
    loop = asyncio.get_running_loop()
    def yt_run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info), info.get('title', 'Video')
    return await loop.run_in_executor(None, yt_run)

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 سلام به ربات پردازش رسانه خوش آمدید!\n\n"
        "🔗 لینک ویدیو را بفرستید.",
        reply_markup=main_keyboard,
        parse_mode="Markdown"
    )

@dp.message(F.text.startswith("http"))
async def link_download(message: types.Message):
    status = await message.answer("⏳ در حال دانلود...")
    url = message.text.strip().split()[0]
    out_file = str(STORAGE_DIR / f"{int(time.time())}_{message.from_user.id}.%(ext)s")
    
    try:
        file_path, title = await download_media(url, out_file)
        await status.edit_text("📤 در حال آپلود...")
        filename = Path(file_path).name
        
        await message.answer_video(
            video=FSInputFile(file_path),
            caption=f"🎬 **{title}**",
            reply_markup=get_media_keyboard(filename),
            parse_mode="Markdown"
        )
        await status.delete()
    except Exception as e:
        await status.edit_text(f"❌ خطا: {str(e)[:150]}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("🚀 Bot Started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
