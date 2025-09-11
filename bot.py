import os
import logging
import random
import requests
import asyncio
from flask import Flask, request
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

# --- 2. Flask 웹서버 생성 ---
# 렌더의 'Start Command'가 실행할 실제 프로그램은 바로 이 'app'입니다.
app = Flask(__name__)

# --- 3. 텔레그램 봇 어플리케이션 설정 ---
ptb_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# --- 4. 웹 주소(라우트) 설정 ---
@app.route("/health_check")
def health_check():
    """UptimeRobot이 방문할 '정문'. 'OK'와 200 성공 코드를 반환합니다."""
    return "OK", 200

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
async def webhook():
    """텔레그램이 업데이트를 보내줄 '비밀 통로'."""
    update_data = request.get_json(force=True)
    update = Update.de_json(data=update_data, bot=ptb_app.bot)
    await ptb_app.process_update(update)
    return "OK", 200

# --- 5. 키보드 메뉴 및 봇 기능 함수들 ---
def get_main_reply_keyboard():
    """메인 메뉴 키보드를 생성합니다."""
    keyboard = [
        [KeyboardButton("📝 1초 회원가입"), KeyboardButton("🔑 사이트 바로가기")],
        [KeyboardButton("👤 계정정보 확인"), KeyboardButton("🔒 비밀번호 변경")],
        [KeyboardButton("📞 고객센터"), KeyboardButton("📘 이용가이드")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_submenu_keyboard():
    """사이트 접속 하위 메뉴 키보드를 생성합니다."""
    keyboard = [
        [KeyboardButton("🚀 사이트 접속하기 (미니앱)", web_app=WebAppInfo(url=MINI_APP_URL))],
        [KeyboardButton("↩️ 메인 메뉴로")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """메인 메뉴를 표시합니다."""
    await update.message.reply_text("마켓 봇에 오신 것을 환영합니다!", reply_markup=get_main_reply_keyboard())

async def enter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """하위 메뉴를 표시합니다."""
    if not MINI_APP_URL:
        await update.message.reply_text("오류: 미니앱 주소가 설정되지 않았습니다.")
        return
    await update.message.reply_text("사이트 접속 메뉴입니다.", reply_markup=get_submenu_keyboard())

async def launch_and_return(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """미니앱 버튼 클릭을 감지하고 메인 메뉴로 복귀시킵니다."""
    if update.message.web_app_data:
        await update.message.reply_text("메인 메뉴로 돌아왔습니다.", reply_markup=get_main_reply_keyboard())

async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'📝 1초 회원가입' 메시지에 응답합니다."""
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
    """'👤 계정정보 확인' 메시지에 응답합니다."""
    user = update.effective_user
    await update.message.reply_text(f"👤 회원정보\n\n• 아이디: {user.username}\n• 닉네임: {user.first_name or '사용자'}\n\n비밀번호 관련 사항은 '비밀번호 변경' 메뉴를 이용해주세요.")

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """고객센터 버튼을 처리합니다."""
    await update.message.reply_text("아래 버튼을 눌러 이동하세요.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("고객센터 문의하기", url=CONTACT_URL)]]))

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """이용가이드 버튼을 처리합니다."""
    await update.message.reply_text("아래 버튼을 눌러 이동하세요.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("공지채널 바로가기", url=GUIDE_URL)]]))

# 비밀번호 변경 대화 관련 함수들
OLD_PASSWORD, NEW_PASSWORD = range(2)
async def changepw_start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("현재 비밀번호를 입력하세요. (/cancel 로 취소)", reply_markup=ReplyKeyboardRemove()); return OLD_PASSWORD
async def received_old_password(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("새 비밀번호를 입력하세요."); return NEW_PASSWORD
async def received_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("비밀번호 변경이 완료되었습니다!", reply_markup=get_main_reply_keyboard()); return ConversationHandler.END
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("취소했습니다.", reply_markup=get_main_reply_keyboard()); return ConversationHandler.END

# --- 6. 봇 핸들러(명령어 인식) 등록 ---
conv_handler = ConversationHandler(entry_points=[MessageHandler(filters.Regex('^🔒 비밀번호 변경$'), changepw_start)], states={OLD_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_old_password)], NEW_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_password)],}, fallbacks=[CommandHandler('cancel', cancel)])
ptb_app.add_handler(CommandHandler("start", start)); ptb_app.add_handler(MessageHandler(filters.Regex('^📝 1초 회원가입$'), signup)); ptb_app.add_handler(MessageHandler(filters.Regex('^🔑 사이트 바로가기$'), enter)); ptb_app.add_handler(MessageHandler(filters.Regex('^👤 계정정보 확인$'), account)); ptb_app.add_handler(MessageHandler(filters.Regex('^📞 고객센터$'), contact)); ptb_app.add_handler(MessageHandler(filters.Regex('^📘 이용가이드$'), guide)); ptb_app.add_handler(MessageHandler(filters.Regex('^↩️ 메인 메뉴로$'), start)); ptb_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, launch_and_return)); ptb_app.add_handler(conv_handler)

# --- 7. 텔레그램 웹훅 설정 (최초 1회만 실행하면 됨) ---
# Gunicorn이 웹서버를 실행하므로, 이 스크립트를 직접 실행하면 웹훅을 설정하는 용도로 사용됩니다.
if __name__ == "__main__":
    async def main_setup():
        await ptb_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
        logger.info(f"Webhook has been set to {WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
    asyncio.run(main_setup())
