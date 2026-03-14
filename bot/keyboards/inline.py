from datetime import datetime, timedelta

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_stadium_list_kb(stadium_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ℹ️ Batafsil", callback_data=f"det_{stadium_id}"),
            InlineKeyboardButton(text="⚡️ Bron qilish", callback_data=f"st_book_{stadium_id}")
        ]
    ])


def get_stadium_detail_kb(stadium_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡️ Bron qilish", callback_data=f"st_book_{stadium_id}")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"backst_{stadium_id}")]
    ])


def get_days_keyboard(stadium_id=None):
    builder = InlineKeyboardBuilder()
    start_date = datetime.now()

    for i in range(30):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        display_text = current_date.strftime("%d-%b")

        if stadium_id and stadium_id != "search":
            callback_data = f"day_{date_str}_{stadium_id}"
        else:
            callback_data = f"day_{date_str}"  # UUID yo'q, Telegram 400 xatosi bermaydi

        builder.button(text=display_text, callback_data=callback_data)

    builder.adjust(4)
    return builder.as_markup()


def get_slots_keyboard(stadium_id, date_str, start_h, end_h, booked_slots, selected_slots=None):
    if selected_slots is None:
        selected_slots = []

    builder = InlineKeyboardBuilder()
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_hour = now.hour

    for hour in range(start_h, end_h):
        time_str = f"{hour:02d}:00"

        # 1. O'tib ketgan vaqtlar (faqat bugun uchun)
        if date_str == current_date and hour <= current_hour:
            continue

        is_booked = any(time_str in str(s) for s in booked_slots)

        if is_booked:
            builder.button(text=f"❌ {time_str}", callback_data="busy")
        else:
            text = f"🟡 {time_str} ✅" if time_str in selected_slots else f"⚪️ {time_str}"

            builder.button(
                text=text,
                callback_data=f"tgl_{stadium_id}_{time_str}"
            )

    builder.adjust(3)

    if selected_slots:
        builder.row(InlineKeyboardButton(
            text=f"🔍 Qidirish ({len(selected_slots)} soat)" if stadium_id == "search" else f"✅ Band qilish ({len(selected_slots)} soat)",
            callback_data=f"cnf_bk_{stadium_id}")
        )

    back_data = f"back_to_st_{stadium_id}" if stadium_id != "search" else "back_to_date_search"
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_data))

    return builder.as_markup()
