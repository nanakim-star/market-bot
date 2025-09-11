import os
import logging
import random
import requests
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
from dotenv import load_dotenv

# --- 1. 기본 설정 및 환경 변수 로드 ---
load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBSITE_API_URL = os.getenv("WEBSITE_API_URL")
CONTACT_URL = os.getenv("CONTACT_URL")
GUIDE_URL = os.getenv("GUIDE_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MINI_APP_URL = os.getenv("MINI_APP_URL")

# --- 2. 텔레그램 봇 어플리케이션 설정 ---
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# --- 3. 키보드 메뉴 및 봇 기능 함수들 ---
def get_main_reply_keyboard():
    keyboard = [[KeyboardButton("📝 1초 회원가입"), KeyboardButton("🔑 사이트 바로가기")], [KeyboardButton("👤 계정정보 확인"), KeyboardButton("🔒 비밀번호 변경")], [KeyboardButton("📞 고객센터"), KeyboardButton("📘 이용가이드")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_submenu_keyboard():
    keyboard = [[KeyboardButton("🚀 사이트 접속하기 (미니앱)", web_app=WebAppInfo(url=MINI_APP_URL))], [KeyboardButton("↩️ 메인 메뉴로")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("마켓 봇에 오신 것을 환영합니다!", reply_markup=get_main_reply_keyboard())

async def enter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("사이트 접속 메뉴입니다.", reply_markup=get_submenu_keyboard())

async def launch_and_return(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.web_app_data: await update.message.reply_text("메인 메뉴로 돌아왔습니다.", reply_markup=get_main_reply_keyboard())

async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user.username: await update.message.reply_text("가입을 위해 텔레그램 사용자명을 설정해주세요."); return
    password, payout_password = str(random.randint(100000, 999999)), str(random.randint(1000, 9999))
    user_data = {"telegram_id": user.id, "username": user.username, "first_name": user.first_name or "사용자", "password": password, "payout_password": payout_password}
    try:
        response = requests.post(WEBSITE_API_URL, json=user_data); response.raise_for_status()
        await update.message.reply_text(f"🎉 가입을 환영합니다!\n\n• 아이디: {user.username}\n• 닉네임: {user.first_name or '사용자'}\n• 비밀번호: {password}\n• 출금 비밀번호: {payout_password}", reply_markup=get_main_reply_keyboard())
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error: {e}"); await update.message.reply_text("서버 오류가 발생했습니다.", reply_markup=get_main_reply_keyboard())

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"👤 회원정보\n\n• 아이디: {user.username}\n• 닉네임: {user.first_name or '사용자'}\n\n비밀번호 관련 사항은 '비밀번호 변경' 메뉴를 이용해주세요.")

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("아래 버튼을 눌러 이동하세요.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("고객센터 문의하기", url=CONTACT_URL)]]))

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("아래 버튼을 눌러 이동하세요.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("공지채널 바로가기", url=GUIDE_URL)]]))

OLD_PASSWORD, NEW_PASSWORD = range(2)
async def changepw_start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("현재 비밀번호를 입력하세요. (/cancel 로 취소)", reply_markup=ReplyKeyboardRemove()); return OLD_PASSWORD
async def received_old_password(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("새 비밀번호를 입력하세요."); return NEW_PASSWORD
async def received_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("비밀번호 변경이 완료되었습니다!", reply_markup=get_main_reply_keyboard()); return ConversationHandler.END
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("취소했습니다.", reply_markup=get_main_reply_keyboard()); return ConversationHandler.END

conv_handler = ConversationHandler(entry_points=[MessageHandler(filters.Regex('^🔒 비밀번호 변경$'), changepw_start)], states={OLD_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_old_password)], NEW_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_password)],}, fallbacks=[CommandHandler('cancel', cancel)])
application.add_handler(CommandHandler("start", start)); application.add_handler(MessageHandler(filters.Regex('^📝 1초 회원가입$'), signup)); application.add_handler(MessageHandler(filters.Regex('^🔑 사이트 바로가기$'), enter)); application.add_handler(MessageHandler(filters.Regex('^👤 계정정보 확인$'), account)); application.add_handler(MessageHandler(filters.Regex('^📞 고객센터$'), contact)); application.add_handler(MessageHandler(filters.Regex('^📘 이용가이드$'), guide)); application.add_handler(MessageHandler(filters.Regex('^↩️ 메인 메뉴로$'), start)); application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, launch_and_return)); application.add_handler(conv_handler)

# --- 렌더에서 봇 실행을 위한 메인 함수 ---
def main() -> None:
    PORT = int(os.environ.get('PORT', 8443))
    logger.info(f"Bot starting with webhook on port {PORT}...")
    application.run_webhook(listen="0.0.0.0", port=PORT, url_path=TELEGRAM_BOT_TOKEN, webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")

if __name__ == "__main__":
    main()
