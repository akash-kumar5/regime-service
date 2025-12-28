import os
import time
import json
import requests
from typing import Dict

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# -------------------------
# CONFIG
# -------------------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = "http://127.0.0.1:8000/current-regime"

BASE_DIR = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(BASE_DIR, "user_settings.json")

REGIMES = [
    "STRONG_UPTREND",
    "WEAK_UPTREND",
    "RANGE",
    "SQUEEZE",
    "WEAK_DOWNTREND",
    "STRONG_DOWNTREND",
]

ALERT_TYPES = [
    "STRONG_TREND_CONFIRMED",
    "CHOPPY_MARKET_WARNING",
    "REGIME_CHANGE",
]

# -------------------------
# STORAGE
# -------------------------

def load_settings() -> Dict:
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(data: Dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user_settings(chat_id: int) -> Dict:
    settings = load_settings()
    cid = str(chat_id)

    if cid not in settings:
        settings[cid] = {
            "alerts": {a: False for a in ALERT_TYPES},
            "regime_notify": {r: False for r in REGIMES},
            "last_regime_sent": None,
        }
        save_settings(settings)

    return settings[cid]

# -------------------------
# KEYBOARDS
# -------------------------

def build_alert_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    s = get_user_settings(chat_id)["alerts"]

    keyboard = []
    for a in ALERT_TYPES:
        status = "ON" if s[a] else "OFF"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{a.replace('_', ' ').title()}: {status}",
                callback_data=f"TOGGLE_ALERT_{a}",
            )
        ])

    return InlineKeyboardMarkup(keyboard)

def build_regime_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    s = get_user_settings(chat_id)["regime_notify"]

    keyboard = []
    for r in REGIMES:
        status = "ON" if s[r] else "OFF"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{r.replace('_', ' ').title()}: {status}",
                callback_data=f"TOGGLE_REGIME_{r}",
            )
        ])

    return InlineKeyboardMarkup(keyboard)

# -------------------------
# COMMANDS
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome.\n\n"
        "Commands:\n"
        "/alerts  – event-based alerts\n"
        "/regimes – regime entry alerts\n"
        "/status  – current market state"
    )

async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "Toggle alert notifications:",
        reply_markup=build_alert_keyboard(chat_id),
    )

async def regimes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "Notify me when market enters:",
        reply_markup=build_regime_keyboard(chat_id),
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = requests.get(API_URL, timeout=5).json()
        msg = (
            f"Symbol: {data['symbol']}\n"
            f"Regime: {data['current_regime']}\n"
            f"Confidence: {data['confidence']:.2f}\n"
            f"Updated: {data['timestamp']}"
        )
    except Exception:
        msg = "Failed to fetch current regime."

    await update.message.reply_text(msg)

# -------------------------
# BUTTON HANDLER
# -------------------------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id
    data = query.data

    settings = load_settings()
    user = get_user_settings(chat_id)

    # ALERT TOGGLE
    if data.startswith("TOGGLE_ALERT_"):
        alert = data.replace("TOGGLE_ALERT_", "")
        user["alerts"][alert] = not user["alerts"][alert]
        settings[str(chat_id)] = user
        save_settings(settings)

        await query.edit_message_reply_markup(
            reply_markup=build_alert_keyboard(chat_id)
        )
        await query.answer()
        return

    # REGIME TOGGLE
    if data.startswith("TOGGLE_REGIME_"):
        regime = data.replace("TOGGLE_REGIME_", "")
        user["regime_notify"][regime] = not user["regime_notify"][regime]
        settings[str(chat_id)] = user
        save_settings(settings)

        await query.edit_message_reply_markup(
            reply_markup=build_regime_keyboard(chat_id)
        )
        await query.answer()
        return

# -------------------------
# MAIN
# -------------------------

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not set")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alerts", alerts))
    app.add_handler(CommandHandler("regimes", regimes))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Telegram bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
