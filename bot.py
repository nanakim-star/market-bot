import os
import logging
import random
import requests
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, InputMediaPhoto
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
EVENT_IMAGE_FILE_IDS = os.getenv("EVENT_IMAGE_FILE_IDS") # 이벤트 이미지 ID 목록을 위한 새 환경 변수

# --- 2. 텔레그램 봇 어플리케이션 설정 ---
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# --- 3. 대화 상태 정의 ---
ASKING_CODE = range(1)

# --- 4. 키보드 메뉴 및 봇 기능 함수들 ---
def get_main_reply_keyboard():
    keyboard = [
        [KeyboardButton("📝 1초 회원가입"), KeyboardButton("🔑 사이트 바로가기")],
        [KeyboardButton("👤 계정정보 확인"), KeyboardButton("🎉 이벤트안내")],
        [KeyboardButton("📞 고객센터"), KeyboardButton("📘 이용가이드")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_signup_submenu_keyboard():
    keyboard = [
        [KeyboardButton("🎫 가입코드 있습니다.")], [KeyboardButton("👤 가입코드 없이 가입하기")], [KeyboardButton("↩️ 메인 메뉴로")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_submenu_keyboard():
    keyboard = [
        [KeyboardButton("🚀 사이트 접속하기 (미니앱)", web_app=WebAppInfo(url=MINI_APP_URL))], [KeyboardButton("↩️ 메인 메뉴로")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("마켓 봇에 오신 것을 환영합니다!", reply_markup=get_main_reply_keyboard())

async def enter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not MINI_APP_URL:
        await update.message.reply_text("오류: 미니앱 주소가 설정되지 않았습니다.")
        return
    await update.message.reply_text("사이트 접속 메뉴입니다.", reply_markup=get_submenu_keyboard())

async def launch_and_return(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.web_app_data:
        await update.message.reply_text("메인 메뉴로 돌아왔습니다.", reply_markup=get_main_reply_keyboard())

# --- '이벤트안내' 함수 변경 ---
async def event_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'🎉 이벤트안내' 버튼 클릭 시 저장된 이미지 ID로 앨범을 보냅니다."""
    if not EVENT_IMAGE_FILE_IDS:
        await update.message.reply_text("현재 진행중인 이벤트가 없습니다.")
        return
    try:
        # 환경 변수에서 쉼표로 구분된 파일 ID 문자열을 리스트로 변환
        file_ids = [file_id.strip() for file_id in EVENT_IMAGE_FILE_IDS.split(',')]
        
        if not file_ids:
            await update.message.reply_text("이벤트 이미지를 찾을 수 없습니다.")
            return

        # InputMediaPhoto 객체 리스트 생성
        media_group = [InputMediaPhoto(media=file_id) for file_id in file_ids]
        
        # 앨범(미디어 그룹) 전송
        await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media_group)

    except Exception as e:
        logger.error(f"이벤트 앨범 전송 중 오류 발생: {e}")
        await update.message.reply_text("이벤트 정보를 불러오는 데 실패했습니다.")

# --- 회원가입 및 기타 함수들 (이전과 동일) ---
async def _perform_signup(update: Update, context: ContextTypes.DEFAULT_TYPE, recommender: str):
    user = update.effective_user
    if not user.username:
        await update.message.reply_text("가입을 위해 텔레그램 사용자명을 설정해주세요.", reply_markup=get_main_reply_keyboard())
        return

    password, payout_password = str(random.randint(100000, 999999)), str(random.randint(1000, 9999))
    user_data = {
        "telegram_id": user.id, "username": user.username, "first_name": user.first_name or "사용자",
        "password": password, "payout_password": payout_password, "Recommender": recommender
    }
    try:
        response = requests.post(WEBSITE_API_URL, json=user_data)
        response.raise_for_status()
        signup_message = (
            f"🎉 가입을 환영합니다!\n\n"
            f"• 아이디: {user.username}\n• 닉네임: {user.first_name or '사용자'}\n"
            f"• 비밀번호: {password}\n• 출금 비밀번호: {payout_password}"
        )
        await update.message.reply_text(signup_message, reply_markup=get_main_reply_keyboard())
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error: {e}")
        await update.message.reply_text("서버 오류가 발생했습니다.", reply_markup=get_main_reply_keyboard())

async def signup_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("가입 코드 유무를 선택해주세요.", reply_markup=get_signup_submenu_keyboard())

async def ask_for_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("안녕하세요. 가입코드가 있으신경우 가입코드를 입력해주세요", reply_markup=ReplyKeyboardRemove())
    return ASKING_CODE

async def signup_with_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    recommender_code = update.message.text
    await _perform_signup(update, context, recommender=recommender_code)
    return ConversationHandler.END

async def signup_without_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _perform_signup(update, context, recommender="online")

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await start(update, context)
    return ConversationHandler.END

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f"👤 회원정보\n\n• 아이디: {user.username}\n• 닉네임: {user.first_name or '사용자'}")

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("고객센터 문의하기", url=CONTACT_URL)]]
    await update.message.reply_text("아래 버튼을 눌러 이동하세요.", reply_markup=InlineKeyboardMarkup(keyboard))

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("공지채널 바로가기", url=GUIDE_URL)]]
    await update.message.reply_text("아래 버튼을 눌러 이동하세요.", reply_markup=InlineKeyboardMarkup(keyboard))

# --- 5. 봇 핸들러 등록 ---
signup_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex('^🎫 가입코드 있습니다.$'), ask_for_code)],
    states={ASKING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, signup_with_code)],},
    fallbacks=[MessageHandler(filters.Regex('^↩️ 메인 메뉴로$'), back_to_main)],
)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Regex('^📝 1초 회원가입$'), signup_start))
application.add_handler(MessageHandler(filters.Regex('^👤 가입코드 없이 가입하기$'), signup_without_code))
application.add_handler(MessageHandler(filters.Regex('^↩️ 메인 메뉴로$'), start))
application.add_handler(MessageHandler(filters.Regex('^🔑 사이트 바로가기$'), enter))
application.add_handler(MessageHandler(filters.Regex('^👤 계정정보 확인$'), account))
application.add_handler(MessageHandler(filters.Regex('^🎉 이벤트안내$'), event_info))
application.add_handler(MessageHandler(filters.Regex('^📞 고객센터$'), contact))
application.add_handler(MessageHandler(filters.Regex('^📘 이용가이드$'), guide))
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, launch_and_return))
application.add_handler(signup_conv_handler)

# --- 6. 렌더에서 봇 실행을 위한 메인 함수 ---
def main() -> None:
    PORT = int(os.environ.get('PORT', 8443))
    
    logger.info(f"Bot starting with webhook on port {PORT}...")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
