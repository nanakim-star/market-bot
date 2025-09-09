import os
import logging
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
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
WEBSITE_LOGIN_URL = os.getenv("WEBSITE_LOGIN_URL", "https://example.com/login") # 자동로그인 URL
CONTACT_URL = os.getenv("CONTACT_URL", "https://t.me/username") # 고객센터 URL
GUIDE_URL = os.getenv("GUIDE_URL", "https://t.me/channel") # 공지채널 URL


# --- 3. 메뉴 및 버튼 생성 함수 ---
def get_main_menu_keyboard():
    """모든 기능을 포함한 메인 메뉴 인라인 키보드를 생성합니다."""
    keyboard = [
        [InlineKeyboardButton("📝 가입하기", callback_data='signup'), InlineKeyboardButton("🔑 접속하기", callback_data='enter')],
        [InlineKeyboardButton("👤 계정정보", callback_data='account'), InlineKeyboardButton("🔒 비밀번호 변경", callback_data='changepw')],
        [InlineKeyboardButton("🤝 지인추천", callback_data='referral')],
        [InlineKeyboardButton("📞 고객센터", callback_data='contact'), InlineKeyboardButton("📘 이용가이드", callback_data='guide')],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- 4. 명령어 처리 함수들 ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start 명령어 또는 메인 메뉴를 표시합니다."""
    start_message = (
        "마켓 봇에 오신 것을 환영합니다!\n\n"
        "아래 메뉴에서 원하시는 기능을 선택해주세요."
    )
    await update.message.reply_text(start_message, reply_markup=get_main_menu_keyboard())

async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user.username:
        await update.callback_query.message.reply_text("회원가입을 위해 먼저 텔레그램 설정에서 사용자명(@아이디)을 만들어주세요.")
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
        await update.callback_query.message.reply_text(signup_message, parse_mode='Markdown')
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 409:
             await update.callback_query.message.reply_text("이미 가입된 회원입니다. `/enter` 명령어로 접속해주세요.")
        else:
             logger.error(f"HTTP Error: {err}")
             await update.callback_query.message.reply_text("가입 처리 중 서버 오류가 발생했습니다.")
    except requests.exceptions.RequestException as err:
        logger.error(f"Request Error: {err}")
        await update.callback_query.message.reply_text("서버에 연결할 수 없습니다.")

async def enter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """자동로그인 버튼을 제공합니다."""
    # 실제로는 서버에서 1회용 로그인 토큰을 받아와야 합니다.
    # 예시: token = requests.get(f"{WEBSITE_API_URL}/token?user_id={update.effective_user.id}").json()['token']
    # login_url_with_token = f"{WEBSITE_LOGIN_URL}?token={token}"
    keyboard = [[InlineKeyboardButton("마켓 자동로그인", url=WEBSITE_LOGIN_URL)]]
    await update.callback_query.message.reply_text(
        "아래 버튼을 눌러 사이트에 바로 입장하세요.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """사용자의 계정 정보를 보여줍니다."""
    user = update.effective_user
    # 실제로는 서버 DB에서 정보를 가져와야 합니다.
    account_info = (
        f"👤 **요청하신 회원정보입니다.**\n\n"
        f"• **아이디**: `{user.username}`\n"
        f"• **닉네임**: `{user.first_name or '사용자'}`\n\n"
        "비밀번호 관련 사항은 '비밀번호 변경' 메뉴를 이용해주세요."
    )
    await update.callback_query.message.reply_text(account_info, parse_mode='Markdown')

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """지인 추천 링크를 제공합니다."""
    user = update.effective_user
    bot = await context.bot.get_me()
    referral_link = f"https://t.me/{bot.username}?start={user.id}"
    message = (
        f"🤝 **친구에게 봇을 추천하고 혜택을 받으세요!**\n\n"
        f"아래의 개인 추천 링크를 복사하여 친구에게 전달하세요.\n\n"
        f"`{referral_link}`"
    )
    await update.callback_query.message.reply_text(message, parse_mode='Markdown')

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """고객센터 바로가기 버튼을 제공합니다."""
    keyboard = [[InlineKeyboardButton("고객센터 문의하기", url=CONTACT_URL)]]
    await update.callback_query.message.reply_text(
        "문의사항이 있으시면 아래 버튼을 눌러 고객센터로 이동하세요.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """이용가이드(공지채널) 바로가기 버튼을 제공합니다."""
    keyboard = [[InlineKeyboardButton("공지채널 바로가기", url=GUIDE_URL)]]
    await update.callback_query.message.reply_text(
        "봇 이용 방법 및 이벤트는 공지채널을 확인해주세요.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- 5. 비밀번호 변경(ConversationHandler) 관련 함수들 ---
OLD_PASSWORD, NEW_PASSWORD = range(2)

async def changepw_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """비밀번호 변경 절차를 시작합니다."""
    await update.callback_query.message.reply_text("변경을 위해 현재 비밀번호를 입력해주세요. 취소하려면 /cancel 을 입력하세요.")
    return OLD_PASSWORD

async def received_old_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """이전 비밀번호를 받고 새 비밀번호를 요청합니다."""
    context.user_data['old_password'] = update.message.text
    await update.message.reply_text("새로운 비밀번호를 입력해주세요.")
    return NEW_PASSWORD

async def received_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """새 비밀번호를 받고 변경을 완료합니다."""
    old_pw = context.user_data.get('old_password')
    new_pw = update.message.text
    
    # 실제로는 서버 API를 호출하여 비밀번호 변경 로직을 수행해야 합니다.
    # response = requests.post(f"{WEBSITE_API_URL}/change_password", 
    #                          json={"user_id": update.effective_user.id, "old_pw": old_pw, "new_pw": new_pw})
    
    await update.message.reply_text(f"비밀번호 변경이 완료되었습니다!")
    # 대화 종료
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """대화를 취소합니다."""
    await update.message.reply_text("비밀번호 변경을 취소했습니다. '/start'를 눌러 메뉴를 다시 확인하세요.")
    return ConversationHandler.END


# --- 6. 콜백 라우터 ---
async def button_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """인라인 버튼 클릭을 감지하고 적절한 함수로 연결합니다."""
    query = update.callback_query
    await query.answer() # 응답 받았다고 텔레그램에 알림

    command = query.data
    
    # 콜백 데이터를 기반으로 해당 함수를 직접 호출합니다.
    if command == 'signup':
        await signup(update, context)
    elif command == 'enter':
        await enter(update, context)
    elif command == 'account':
        await account(update, context)
    elif command == 'referral':
        await referral(update, context)
    elif command == 'contact':
        await contact(update, context)
    elif command == 'guide':
        await guide(update, context)
    elif command == 'changepw':
        # 비밀번호 변경은 대화형 핸들러를 시작해야 하므로 메시지를 보냅니다.
        await query.message.reply_text("비밀번호 변경을 시작합니다. /changepw 명령어를 직접 입력하거나 메뉴를 다시 클릭해주세요.")


# --- 7. 메인 함수 (봇 실행) ---
def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 비밀번호 변경 대화 핸들러 설정
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(changepw_start, pattern='^changepw$')],
        states={
            OLD_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_old_password)],
            NEW_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler) # 대화 핸들러 추가
    application.add_handler(CallbackQueryHandler(button_callback_router)) # 버튼 콜백 핸들러 추가
    
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
