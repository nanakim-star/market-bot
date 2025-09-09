import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 렌더(Render)에 설정할 봇 토큰을 불러옵니다.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# /start 명령어 처리 함수
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """사용자가 /start 명령어를 보냈을 때 환영 메시지를 보냅니다."""
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
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    logger.info("Bot is starting...")
    # 서버에서 실행할 때는 Webhook 방식으로 변경할 예정입니다.
    # 우선은 Polling으로 테스트합니다.
    application.run_polling()

if __name__ == '__main__':
    main()
