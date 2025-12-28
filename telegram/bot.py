import os
import json
import requests
import asyncio
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
API_URL = os.getenv("REGIME_API_URL", "http://127.0.0.1:8000/current-regime")

BASE_DIR = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(BASE_DIR, "user_settings.json")

REGIMES = [
    "Choppy High-Vol",
    "Range",
    "Squeeze",
    "Strong Trend",
    "Volatility Spike",
    "Weak Trend",
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
        
def normalize_user_settings(user: Dict):
    # Ensure all alerts exist
    for a in ALERT_TYPES:
        user["alerts"].setdefault(a, False)

    # Ensure all regimes exist
    for r in REGIMES:
        user["regime_notify"].setdefault(r, False)


def ensure_user(settings: Dict, chat_id: int) -> Dict:
    cid = str(chat_id)
    if cid not in settings:
        settings[cid] = {
            "alerts": {a: False for a in ALERT_TYPES},
            "regime_notify": {r: False for r in REGIMES},
        }
    else:
        normalize_user_settings(settings[cid])
    return settings[cid]

# -------------------------
# KEYBOARDS
# -------------------------

def build_alert_keyboard(settings: Dict, chat_id: int) -> InlineKeyboardMarkup:
    user = ensure_user(settings, chat_id)
    keyboard = []

    for a in ALERT_TYPES:
        status = "ON" if user["alerts"][a] else "OFF"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{a.replace('_', ' ').title()}: {status}",
                callback_data=f"TOGGLE_ALERT_{a}",
            )
        ])

    return InlineKeyboardMarkup(keyboard)

def build_regime_keyboard(settings: Dict, chat_id: int) -> InlineKeyboardMarkup:
    user = ensure_user(settings, chat_id)
    keyboard = []

    for r in REGIMES:
        status = "ON" if user["regime_notify"][r] else "OFF"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{r}: {status}",
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
        "/alerts  – event alerts\n"
        "/regimes – regime entry alerts\n"
        "/status  – current market regime"
    )

async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = load_settings()
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "Toggle alert notifications:",
        reply_markup=build_alert_keyboard(settings, chat_id),
    )

async def regimes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = load_settings()
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "Notify me when market enters:",
        reply_markup=build_regime_keyboard(settings, chat_id),
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_running_loop()
    try:
        resp = await loop.run_in_executor(
            None, lambda: requests.get(API_URL, timeout=5)
        )
        data = resp.json()
        msg = (
            f"Symbol: {data['symbol']}\n"
            f"Regime: {data['current_regime']}\n"
            f"Confidence: {data['confidence']:.2f}\n"
            f"Timestamp: {data['timestamp']}"
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
    user = ensure_user(settings, chat_id)

    if data.startswith("TOGGLE_ALERT_"):
        alert = data.replace("TOGGLE_ALERT_", "")
        if alert not in user["alerts"]:
            await query.answer("Unknown alert", show_alert=True)
            return

        user["alerts"][alert] = not user["alerts"][alert]
        save_settings(settings)

        await query.edit_message_reply_markup(
            reply_markup=build_alert_keyboard(settings, chat_id)
        )
        await query.answer()
        return

    if data.startswith("TOGGLE_REGIME_"):
        regime = data.replace("TOGGLE_REGIME_", "")
        if regime not in user["regime_notify"]:
            await query.answer("Unknown regime", show_alert=True)
            return

        user["regime_notify"][regime] = not user["regime_notify"][regime]
        save_settings(settings)

        await query.edit_message_reply_markup(
            reply_markup=build_regime_keyboard(settings, chat_id)
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
