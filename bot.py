import os
import logging
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. 기본 설정 ---
# 로그 출력 형식과 레벨을 설정합니다.
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- 2. 환경 변수 불러오기 ---
# Render 대시보드에 설정한 값들을 불러옵니다.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBSITE_API_URL = os.getenv("WEBSITE_API_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


# --- 3. 명령어 처리 함수들 ---

# /start 명령어: 봇 시작 시 환영 메시지를 보냅니다.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("가입하기 (/signup)", callback_data='signup')],
        [InlineKeyboardButton("접속하기 (/enter)", callback_data='enter')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    start_message = (
        "마켓 봇에 오신 것을 환영합니다!\n\n"
        "아래 메뉴를 통해 원하시는 작업을 선택해주세요."
    )
    await update.message.reply_text(start_message, reply_markup=reply_markup)

# /signup 명령어: 회원가입을 처리합니다.
async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    
    # 1. 텔레그램 사용자명(@ID)이 없으면 가입을 거절합니다.
    if not user.username:
        await update.message.reply_text("회원가입을 위해 먼저 텔레그램 설정에서 사용자명(@아이디)을 만들어주세요.")
        return

    # 2. 서버로 보낼 데이터를 준비합니다. (랜덤 비밀번호 생성 포함)
    password = str(random.randint(100000, 999999))
    payout_password = str(random.randint(1000, 9999))
    
    user_data = {
        "telegram_id": user.id,
        "username": user.username,
        "first_name": user.first_name or "사용자", # 이름이 없는 경우 대비
        "password": password,
        "payout_password": payout_password
    }

    # 3. 웹사이트 서버로 데이터를 전송합니다.
    try:
        response = requests.post(WEBSITE_API_URL, json=user_data)
        response.raise_for_status() # HTTP 오류가 발생하면 예외를 일으킵니다.

        # 4. 가입 성공 시, 사용자에게 완료 메시지를 보냅니다.
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
        # 서버에서 오는 에러를 처리합니다. (예: 이미 가입된 회원)
        if err.response.status_code == 409: # 409 Conflict: 중복 리소스
             await update.message.reply_text("이미 가입된 회원입니다. `/enter` 명령어로 접속해주세요.")
        else:
             logger.error(f"HTTP Error: {err}")
             await update.message.reply_text("가입 처리 중 서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    except requests.exceptions.RequestException as err:
        # 네트워크 연결 등 기타 에러를 처리합니다.
        logger.error(f"Request Error: {err}")
        await update.message.reply_text("서버에 연결할 수 없습니다. 관리자에게 문의해주세요.")


# --- 4. 봇 실행 메인 함수 ---
def main() -> None:
    """Webhook 방식으로 봇을 시작합니다."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 사용할 명령어 핸들러들을 등록합니다.
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("signup", signup))

    # Render가 제공하는 포트와 우리가 설정한 웹훅 URL을 사용합니다.
    PORT = int(os.environ.get('PORT', '8443'))

    # 봇을 Webhook 방식으로 실행합니다.
    logger.info(f"Bot starting with webhook on port {PORT}...")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()
