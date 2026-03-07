from aiogram import Router, types, F
from aiogram.filters import Command

from api_client import APIClient
from keyboards.reply import get_phone_keyboard, main_menu

router = Router()
api = APIClient()



@router.message(Command("start"))
async def cmd_start(message: types.Message):
    telegram_id = message.from_user.id

    user_exists = api.check_user_exists(telegram_id)

    if user_exists:
        await message.answer(
            f"Xush kelibsiz, {message.from_user.first_name}! 👋\n"
            "Siz tizimga muvaffaqiyatli kirgansiz. Maydon tanlashingiz mumkin.",
            reply_markup=main_menu()
        )
    else:
        await message.answer(
            "Xush kelibsiz! Botdan foydalanish uchun telefon raqamingizni yuboring.",
            reply_markup=get_phone_keyboard()
        )


@router.message(F.contact)
async def handle_contact(message: types.Message):
    phone = message.contact.phone_number
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name

    status, response = api.register_user(phone, telegram_id, full_name)

    if status in [200, 201]:
        await message.answer(f"✅ Rahmat {full_name}!", reply_markup=main_menu())
    else:
        import json
        error_msg = json.dumps(response, indent=2)
        await message.answer(f"❌ Xatolik (Status: {status}):\n<pre>{error_msg}</pre>", parse_mode="HTML")
