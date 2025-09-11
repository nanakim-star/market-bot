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
EVENT_CHANNEL_ID = os.getenv("EVENT_CHANNEL_ID") # 이벤트 채널 ID를 위한 새 환경 변수

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

async def event_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'🎉 이벤트안내' 버튼 클릭 시 채널의 이미지를 앨범으로 보냅니다."""
    if not EVENT_CHANNEL_ID:
        await update.message.reply_text("현재 진행중인 이벤트가 없습니다.")
        return
    try:
        # 봇이 채널 관리자여야만 get_chat_history를 사용할 수 있습니다.
        # 이 기능은 현재 공식 라이브러리에 없으므로 직접 API를 호출합니다.
        # 대신, 간단하게 채널에 있는 사진을 10장까지 전달하는 방식으로 구현합니다.
        # (더 복잡한 로직은 get_chat_history를 직접 구현해야 합니다)

        # 우선, 간단한 안내 메시지와 채널 링크를 제공하는 방식으로 대체합니다. 
        # (직접 이미지 전달은 봇 권한 상승 및 복잡한 코드 변경이 필요)
        # 만약 이 기능을 꼭 원하시면, 더 복잡한 코드로 변경해 드릴 수 있습니다.

        # ---> 가장 안정적이고 추천드렸던 채널 링크 방식으로 우선 구현합니다.
        # 만약 채널에서 이미지를 직접 가져오는 방식을 원하시면 알려주세요.
        channel_link = await context.bot.create_chat_invite_link(chat_id=EVENT_CHANNEL_ID, member_limit=1)
        keyboard = [[InlineKeyboardButton("이벤트 보러가기", url=channel_link.invite_link)]]
        await update.message.reply_text(
            "다양한 이벤트가 진행중입니다! 아래 버튼을 눌러 확인하세요.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"이벤트 처리 중 오류 발생: {e}")
        await update.message.reply_text("이벤트 정보를 불러오는 데 실패했습니다.")

# --- 회원가입 및 기타 함수들 (이전과 동일) ---
async def _perform_signup(update: Update, context: ContextTypes.DEFAULT_TYPE, recommender: str):
    # ... (내용 생략)
async def signup_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (내용 생략)
async def ask_for_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (내용 생략)
async def signup_with_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (내용 생략)
async def signup_without_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (내용 생략)
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (내용 생략)
async def account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (내용 생략)
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (내용 생략)
async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (내용 생략)

# --- 핸들러 등록 (이전과 동일) ---
# ... (내용 생략)

# --- 메인 함수 (이전과 동일) ---
# ... (내용 생략)
