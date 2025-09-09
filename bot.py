import os
import logging
import random
import requests # requests 라이브러리 추가
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 기본 설정 (이전과 동일) ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 환경 변수 불러오기 (서버 주소 추가) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBSITE_API_URL = os.getenv("WEBSITE_API_URL") # 새로 추가된 부분

# --- 명령어 함수들 ---

# /start 명령어 처리 함수 (이전과 동일)
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

# /signup 명령어 처리 함수 (핵심 기능)
async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    
    # 1. 텔레그램 사용자명(@ID) 확인
    if not user.username:
        await update.message.reply_text("회원가입을 위해 먼저 텔레그램 설정에서 사용자명(@아이디)을 만들어주세요.")
        return

    # 2. 서버로 보낼 데이터 준비
    password = str(random.randint(100000, 999999))
    payout_password = str(random.randint(1000, 9999))
    
    user_data = {
        "telegram_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "password": password,
        "payout_password": payout_password
    }

    # 3. 웹사이트 서버로 데이터 전송
    try:
        # WEBSITE_API_URL 환경 변수를 사용!
        response = requests.post(WEBSITE_API_URL, json=user_data)
        response.raise_for_status() # 오류가 있으면 예외 발생

        # 4. 성공 시 가입 완료 메시지 전송
        signup_message = (
            f"🎉 **마켓 가입을 환영합니다!**\n\n"
            f"* **아이디**: `{user.username}`\n"
            f"* **닉네임**: `{user.first_name}`\n"
            f"* **초기 비밀번호**: `{password}` (봇을 통해 변경 권장)\n"
            f"* **초기 출금 비밀번호**: `{payout_password}` (고객센터 문의)\n\n"
            "🌐 웹사이트에서도 동일 계정으로 로그인 가능합니다."
        )
        # TODO: 여기에 자동로그인 버튼 추가
        await update.message.reply_text(signup_message, parse_mode='Markdown')

    except requests.exceptions.HTTPError as err:
        # 서버에서 오는 에러 처리 (예: 이미 가입된 회원)
        if err.response.status_code == 409: # 409 Conflict: 중복된 리소스
             await update.message.reply_text("이미 가입된 회원입니다. `/enter` 명령어로 접속해주세요.")
        else:
             logger.error(f"HTTP Error: {err}")
             await update.message.reply_text("가입 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    except requests.exceptions.RequestException as err:
        # 네트워크 등 기타 에러 처리
        logger.error(f"Request Error: {err}")
        await update.message.reply_text("서버에 연결할 수 없습니다. 관리자에게 문의해주세요.")


def main() -> None:
    """봇을 시작합니다."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 명령어 핸들러 등록 (/signup 추가)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("signup", signup))
    
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
