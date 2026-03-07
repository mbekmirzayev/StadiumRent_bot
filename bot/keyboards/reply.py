from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏟 Maydonlarni ko'rish")],
            [KeyboardButton(text="🔍 Vaqt bo'yicha qidirish")],
            [KeyboardButton(text="📍 Yaqin maydonlar (GPS)", request_location=True)],
            [KeyboardButton(text="📋 Mening bronlarim")]
        ],
        resize_keyboard=True
    )