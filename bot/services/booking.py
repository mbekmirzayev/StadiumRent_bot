from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api_client import APIClient

router = Router()
api = APIClient()


class BookingStates(StatesGroup):
    waiting_for_start_time = State()
    waiting_for_end_time = State()


@router.callback_query(F.data.startswith("st_book_"))
async def start_booking(callback: types.CallbackQuery, state: FSMContext):
    st_id = callback.data.split("_")[-1]
    await state.update_data(stadium_id=st_id)

    await callback.message.answer(
        "📅 <b>Boshlanish vaqtini kiriting</b>\n"
        "Format: <code>YYYY-MM-DD HH:MM</code>\n"
        "Masalan: <code>2024-05-20 18:00</code>",
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.waiting_for_start_time)
    await callback.answer()


@router.message(BookingStates.waiting_for_start_time)
async def process_start_time(message: types.Message, state: FSMContext):
    await state.update_data(start_time=message.text)
    await message.answer(
        "🏁 <b>Tugash vaqtini kiriting</b>\n"
        "Masalan: <code>2024-05-20 20:00</code>",
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.waiting_for_end_time)


@router.message(BookingStates.waiting_for_end_time)
async def finalize_booking(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    status_msg = await message.answer("Tekshirilmoqda... ⏳")

    auth_data = api.get_token(message.from_user.id)
    if not auth_data:
        await status_msg.edit_text("❌ Siz ro'yxatdan o'tmagansiz!")
        return

    payload = {
        "stadium": user_data.get("stadium_id"),
        "start_time": user_data.get("start_time"),
        "end_time": message.text
    }

    status_code, response_data = api.create_booking(auth_data['access'], payload)

    if status_code == 201:
        price = response_data.get('total_price', '0')
        await status_msg.edit_text(
            f"✅ <b>Muvaffaqiyatli bron qilindi!</b>\n"
            f"💰 Umumiy summa: {price} so'm",
            parse_mode="HTML"
        )
        await state.clear()
    else:
        error = response_data.get('detail') or response_data.get('non_field_errors') or response_data
        await status_msg.edit_text(f"❌ <b>Xatolik:</b>\n{error}", parse_mode="HTML")


@router.message(F.text == "📋 Mening bronlarim")
async def show_my_bookings(message: types.Message):
    auth_data = api.get_token(message.from_user.id)
    if not auth_data:
        await message.answer("Siz hali ro'yxatdan o'tmagansiz.")
        return

    bookings = api.get_my_bookings(auth_data['access'])
    if not bookings:
        await message.answer("Sizda hali bronlar mavjud emas.")
        return

    await message.answer("📑 <b>Sizning bronlaringiz:</b>", parse_mode="HTML")

    for b in bookings:
        st_details = b.get('stadium_details', {})
        status = "❌ Bekor qilingan" if b['is_canceled'] else "✅ Faol"

        start = b['start_time'].replace('T', ' ')[:16]
        end = b['end_time'].replace('T', ' ')[:16]

        caption = (
            f"🏟 <b>{st_details.get('name')}</b>\n"
            f"📍 Manzil: {st_details.get('address')}\n"
            f"📅 Vaqt: {start} — {end}\n"
            f"💰 Jami: {b['total_price']:,} so'm\n"
            f"<b>Holati:</b> {status}"
        ).replace(",", " ")

        builder = InlineKeyboardBuilder()

        lat, lon = st_details.get('lat'), st_details.get('lon')
        if lat and lon:
            builder.button(text="📍 Xaritada ko'rish", callback_data=f"show_loc_{lat}_{lon}")

        if not b['is_canceled']:
            builder.button(text="🚫 Bekor qilish", callback_data=f"cancel_bk_{b['id']}")

        builder.adjust(1)
        await message.answer(caption, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("show_loc_"))
async def send_location(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    await callback.message.answer_location(latitude=float(parts[2]), longitude=float(parts[3]))
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_bk_"))
async def process_cancel(callback: types.CallbackQuery):
    bk_id = callback.data.split("_")[2]
    auth_data = api.get_token(callback.from_user.id)

    status = api.cancel_booking(auth_data['access'], bk_id)
    if status == 200:
        await callback.answer("Bron bekor qilindi!", show_alert=True)
        await callback.message.edit_text(callback.message.text + "\n\n⚠️ <b>BEKOR QILINDI</b>", parse_mode="HTML")
    else:
        await callback.answer("Xatolik! Bekor qilib bo'lmadi.", show_alert=True)
