from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api_client import APIClient
from bot.keyboards.inline import get_days_keyboard

router = Router()
api = APIClient()


@router.callback_query(F.data.startswith("st_book_"))
async def start_booking_process(callback: types.CallbackQuery, state: FSMContext):
    st_id = callback.data.split("_")[-1]
    await state.update_data(stadium_id=st_id)

    await callback.message.edit_text(
        "📅 <b>Bron qilish uchun sana tanlang:</b>",
        reply_markup=get_days_keyboard(st_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cnf_bk_"))
async def show_pre_confirmation(callback: types.CallbackQuery, state: FSMContext):
    stadium_id = callback.data.replace("cnf_bk_", "")

    data = await state.get_data()
    slots = data.get("selected_slots", [])

    if not slots:
        await callback.answer("Vaqt tanlanmagan!", show_alert=True)
        return

    if stadium_id == "search":
        search_date = data.get("search_date")

        start_time = slots[0]

        last_hour = int(slots[-1].split(":")[0])
        end_time = f"{last_hour + 1:02d}:00"

        await callback.message.edit_text(
            f"🔍 <b>{search_date}</b> kuni <b>{start_time} — {end_time}</b> oraliqdagi bo'sh stadionlar qidirilmoqda...",
            parse_mode="HTML"
        )

        stadiums = api.search_by_time(
            date=search_date,
            start_time=start_time,
            end_time=end_time
        )
        print(f"DEBUG: API dan kelgan ma'lumot -> {stadiums}")
        if not stadiums:
            await callback.message.answer("😔 Afsuski, bu vaqtda bo'sh stadionlar topilmadi.")
            return
        for st in stadiums:
            text = (f"🏟 <b>{st.get('name', 'Nomsiz stadion')}</b>\n"
                    f"💰 Narxi: {st.get('price', 'Noma\'lum')} so'm\n"
                    f"📍 Manzil: {st.get('address', 'Manzil ko\'rsatilmagan')}")

            builder = InlineKeyboardBuilder()
            builder.button(text="👁 Ko'rish", callback_data=f"stadium_{st.get('id')}")

            image = st.get('image') or st.get('image_url')
            if image and not image.startswith('http://127.0.0.1'):
                await callback.message.answer_photo(photo=image, caption=text, reply_markup=builder.as_markup(),
                                                    parse_mode="HTML")
            else:
                await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        return

    booking_date = data.get("booking_date")
    start_time = slots[0]
    end_hour = int(slots[-1].split(":")[0]) + 1
    end_time = f"{end_hour:02d}:00"

    text = (f"🏟 <b>Bronni tasdiqlaysizmi?</b>\n\n"
            f"📅 Sana: <code>{booking_date}</code>\n"
            f"⏰ Vaqt: <code>{start_time} — {end_time}</code>\n"
            f"⏳ Davomiyligi: <code>{len(slots)} soat</code>")

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data="final_booking_api")
    builder.button(text="❌ Bekor qilish", callback_data="cancel_process")
    builder.adjust(2)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "final_booking_api")
async def final_confirm_booking(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    stadium_id = user_data.get('stadium_id')
    date = user_data.get('booking_date')
    slots = user_data.get('selected_slots', [])

    print(f"DEBUG: st_id={stadium_id}, date={date}, slots={slots}")

    if not all([stadium_id, date, slots]):
        await callback.answer("Ma'lumotlar yetarli emas, iltimos qaytadan urinib ko'ring.", show_alert=True)
        return

    if not slots:
        await callback.answer("Vaqt tanlanmagan!")
        return

    start_time = slots[0]
    end_hour = int(slots[-1].split(":")[0]) + 1
    end_time = f"{end_hour:02d}:00"

    date = user_data['booking_date']
    full_start = f"{date} {start_time}:00"
    full_end = f"{date} {end_time}:00"

    auth_data = api.get_token(callback.from_user.id)
    payload = {
        "stadium": stadium_id,
        "start_time": full_start,
        "end_time": full_end
    }

    status_code, response_data = api.create_booking(auth_data['access'], payload)

    if status_code == 201:
        price = response_data.get('total_price', '0')
        await callback.message.edit_text(
            f"✅ <b>Muvaffaqiyatli bron qilindi!</b>\n"
            f"📅 Sana: <code>{date}</code>\n"
            f"⏰ Vaqt: <code>{start_time} - {end_time}</code>\n"
            f"💰 Jami summa: {price:,} so'm".replace(",", " "),
            parse_mode="HTML"
        )
        await state.clear()
    else:
        error = response_data.get('detail') or "Xatolik yuz berdi"
        await callback.message.answer(f"❌ <b>Xatolik:</b>\n{error}", parse_mode="HTML")


@router.callback_query(F.data == "cancel_process")
async def cancel_booking(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bron qilish bekor qilindi.")


@router.callback_query(F.data == "busy")
async def slot_busy_handler(callback: types.CallbackQuery):
    await callback.answer("Bu vaqt band! Iltimos boshqasini tanlang.", show_alert=True)


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
    await callback.message.answer_location(latitude=float(parts[2]), longitude=float(parts[3]),
                                           reply_to_message_id=callback.message.message_id)
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
