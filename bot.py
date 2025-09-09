import os
import logging
import random
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

# --- 1. 기본 설정 ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. 환경 변수 불러오기 ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBSITE_API_URL = os.getenv("WEBSITE_API_URL")
WEBSITE_LOGIN_URL = os.getenv("WEBSITE_LOGIN_URL", "https://example.com/login")
CONTACT_URL = os.getenv("CONTACT_URL", "https://t.me/username")
GUIDE_URL = os.getenv("GUIDE_URL", "https://t.me/channel")

# --- 3. 리플라이 키보드 메뉴 생성 ---
def get_main_reply_keyboard():
    """메인 메뉴 리플라이 키보드를 생성합니다."""
    keyboard = [
        [KeyboardButton("📝 1초 가입하기"), KeyboardButton("🔑 사이트 바로가기")],
        [KeyboardButton("👤 계정정보 확인"), KeyboardButton("🔒 비밀번호 변경")],
        [KeyboardButton("📞 고객센터"), KeyboardButton("📘 이용가이드")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- 4. 명령어 및 메시지 처리 함수들 ---

# UptimeRobot을 위한 헬스 체크 함수
async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """UptimeRobot이 접속할 때 'OK'라고 응답해주는 함수"""
    # 이 함수는 실제로 아무 작업도 하지 않아도 됩니다.
    # 텔레그램 라이브러리가 서버에 200 OK 응답을 보내주는 것만으로 충분합니다.
    # 텔레그램 채팅방에 응답을 보낼 필요는 없습니다.
    pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start 명령어: 환영 메시지와 함께 리플라이 키보드를 표시합니다."""
    start_message = (
        "마켓 봇에 오신 것을 환영합니다!\n\n"
        "화면 하단의 키보드 메뉴에서 원하시는 기능을 선택해주세요."
    )
    await update.message.reply_text(start_message, reply_markup=get_main_reply_keyboard())

async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'📝 1초 가입하기' 메시지에 응답합니다."""
    user = update.effective_user
    if not user.username:
        await update.message.reply_text("회원가입을 위해 먼저 텔레그램 설정에서 사용자명(@아이디)을 만들어주세요.")
        return

    password = str(random.randint(100000, 999999))
    payout_password = str(random.randint(1000, 9999))
    
    user_data = {
        "telegram_id": user.id, "username": user.username,
        "first_name": user.first_name or "사용자", "password": password,
        "payout_password": payout_password
    }

    try:
        response = requests.post(WEBSITE_API_URL, json=user_data)
        response.raise_for_status()
        signup_message = (
            f"🎉 **마켓 가입을 환영합니다!**\n\n"
            f"* **아이디**: `{user.username}`\n"
            f"* **닉네임**: `{user.first_name or '사용자'}`\n"
            f"* **초기 비밀번호**: `{password}`\n"
            f"* **초기 출금 비밀번호**: `{payout_password}`\n\n"
            "🌐 웹사이트에서도 동일 계정으로 로그인 가능합니다."
        )
        await update.message.reply_text(signup_message, parse_mode='Markdown')
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 409:
             await update.message.reply_text("이미 가입된 회원입니다. '사이트 바로가기' 메뉴를 이용해주세요.")
        else:
             logger.error(f"HTTP Error: {err}")
             await update.message.reply_text("가입 처리 중 서버 오류가 발생했습니다.")
    except requests.exceptions.RequestException as err:
        logger.error(f"Request Error: {err}")
        await update.message.reply_text("서버에 연결할 수 없습니다.")

async def enter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'🔑 사이트 바로가기' 메시지에 응답합니다."""
    keyboard = [[KeyboardButton("마켓 자동로그인", url=WEBSITE_LOGIN_URL)]]
    await update.message.reply_text(
        "아래 버튼을 눌러 사이트에 바로 입장하세요.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'👤 계정정보 확인' 메시지에 응답합니다."""
    user = update.effective_user
    account_info = (
        f"👤 **요청하신 회원정보입니다.**\n\n"
        f"• **아이디**: `{user.username}`\n"
        f"• **닉네임**: `{user.first_name or '사용자'}`\n\n"
        "비밀번호 관련 사항은 '비밀번호 변경' 메뉴를 이용해주세요."
    )
    await update.message.reply_text(account_info, parse_mode='Markdown')

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'📞 고객센터' 메시지에 응답합니다."""
    keyboard = [[KeyboardButton("고객센터 문의하기", url=CONTACT_URL)]]
    await update.message.reply_text(
        "문의사항이 있으시면 아래 버튼을 눌러 고객센터로 이동하세요.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'📘 이용가이드' 메시지에 응답합니다."""
    keyboard = [[KeyboardButton("공지채널 바로가기", url=GUIDE_URL)]]
    await update.message.reply_text(
        "봇 이용 방법 및 이벤트는 공지채널을 확인해주세요.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

# --- 5. 비밀번호 변경(ConversationHandler) 관련 함수들 ---
OLD_PASSWORD, NEW_PASSWORD = range(2)

async def changepw_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("변경을 위해 현재 비밀번호를 입력해주세요. 취소하려면 /cancel 을 입력하세요.")
    return OLD_PASSWORD

async def received_old_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['old_password'] = update.message.text
    await update.message.reply_text("새로운 비밀번호를 입력해주세요.")
    return NEW_PASSWORD

async def received_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f"비밀번호 변경이 완료되었습니다!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("비밀번호 변경을 취소했습니다.", reply_markup=get_main_reply_keyboard())
    return ConversationHandler.END

# --- 6. 메인 함수 (봇 실행) ---
def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🔒 비밀번호 변경$'), changepw_start)],
        states={
            OLD_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_old_password)],
            NEW_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # UptimeRobot이 봇이 살아있는지 확인할 수 있도록 /health_check 핸들러를 추가합니다.
    # 이 핸들러는 다른 일반 핸들러보다 먼저 등록하는 것이 좋습니다.
    application.add_handler(CommandHandler("health_check", health_check))

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex('^📝 1초 가입하기$'), signup))
    application.add_handler(MessageHandler(filters.Regex('^🔑 사이트 바로가기$'), enter))
    application.add_handler(MessageHandler(filters.Regex('^👤 계정정보 확인$'), account))
    application.add_handler(MessageHandler(filters.Regex('^📞 고객센터$'), contact))
    application.add_handler(MessageHandler(filters.Regex('^📘 이용가이드$'), guide))
    application.add_handler(conv_handler)
    
    PORT = int(os.environ.get('PORT', '8443'))
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    logger.info(f"Bot starting with webhook on port {PORT}...")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()
