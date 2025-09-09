import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# .env 파일에서 환경 변수 불러오기
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# /start 명령어 처리 함수
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """사용자가 /start 명령어를 보냈을 때 환영 메시지를 보냅니다."""
    
    # 메뉴 버튼 (나중에 기능 추가 예정)
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

def main() -> None:
    """봇을 시작합니다."""
    # Application 객체 생성
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # /start 명령어 핸들러 등록
    application.add_handler(CommandHandler("start", start))
    
    # 봇 실행 (로컬 테스트를 위해 폴링 방식으로 시작)
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
