from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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