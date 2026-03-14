from aiogram import F, types
from aiogram import Router
from aiogram.fsm.context import FSMContext

from api_client import APIClient
from keyboards.inline import get_stadium_detail_kb, get_stadium_list_kb, get_slots_keyboard, get_days_keyboard

router = Router()
api = APIClient()


@router.message(F.text == "🏟 Maydonlarni ko'rish")
async def list_stadiums(message: types.Message):
    await message.answer("🔍 Maydonlar ro'yxati yuklanmoqda...")
    stadiums = api.get_stadiums()

    if not stadiums:
        await message.answer("Hozircha maydonlar yo'q.")
        return

    for st in stadiums:
        price = float(st['price_per_hour'])

        caption = (
            f"🏟 <b>{st['name']}</b>\n\n"
            f"📍 Manzil: {st['address']}\n"
            f"💰 Narxi: {price:,.0f} so'm/soat\n"
        ).replace(",", " ")

        kb = get_stadium_list_kb(st['id'])
        img_url = st.get('image')

        if img_url and "127.0.0.1" in img_url:
            print(f"⚠️ OGOHLANTIRISH: Telegram {img_url} manzilidan rasm ololmaydi!")

        try:
            if img_url and not img_url.endswith('.html'):
                await message.answer_photo(photo=img_url, caption=caption, reply_markup=kb, parse_mode="HTML")
            else:
                await message.answer(text=caption + "\n<i>(Rasm yuklanmadi)</i>", reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            print(f"Rasmda xato: {e}")
            await message.answer(text=caption, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("det_"))
async def show_stadium_detail(callback: types.CallbackQuery):
    stadium_id = callback.data.split("_")[1]
    st = api.get_stadium_detail(stadium_id)

    if not st:
        await callback.answer("Ma'lumot topilmadi!", show_alert=True)
        return

    expanded_text = (
        f"🏟 <b>{st.get('name', 'Nomsiz')}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📍 <b>Manzil:</b> {st.get('address', 'Kiritilmagan')}\n"
        f"💰 <b>Narxi:</b> {float(st.get('price_per_hour', 0)):,.0f} so'm/soat\n"
        f"📞 <b>Aloqa:</b> {st.get('contact', 'Mavjud emas')}\n"
        f"🕒 <b>Ish vaqti:</b> {st.get('open_at', '--:--')} - {st.get('closed_at', '--:--')}\n"
        f"👤 <b>Admin:</b> {st.get('owner_name', 'Noma\'lum')}\n"
        f"📞 <b>Admin raqami:</b> {st.get('owner_phone', 'Mavjud emas')}\n"
        f"📝 <b>Tavsif:</b> {st.get('description', 'Ma\'lumot berilmagan')}\n"
    ).replace(",", " ")

    kb = get_stadium_detail_kb(stadium_id)

    if callback.message.caption:
        await callback.message.edit_caption(caption=expanded_text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text(text=expanded_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("backst_"))
async def back_to_short_list(callback: types.CallbackQuery):
    stadium_id = callback.data.split("_")[-1]
    st = api.get_stadium_detail(stadium_id)

    short_text = (
        f"🏟 <b>{st.get('name', 'Nomsiz')}</b>\n\n"
        f"📍 Manzil: {st.get('address', 'Kiritilmagan')}\n"
        f"💰 Narxi: {float(st.get('price_per_hour', 0)):,.0f} so'm/soat"
    ).replace(",", " ")

    kb = get_stadium_list_kb(stadium_id)

    if callback.message.caption:
        await callback.message.edit_caption(caption=short_text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text(text=short_text, reply_markup=kb, parse_mode="HTML")

    await callback.answer()


from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


@router.message(F.text == "📍 Yaqin maydonlar")
async def ask_location(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📍 Lokatsiyamni yuborish", request_location=True)
    builder.button(text="⬅️ Bosh menyu")
    builder.adjust(1)

    await message.answer(
        "Yaqin atrofdagi maydonlarni topish uchun lokatsiyangizni yuboring:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )


@router.message(F.location)
async def handle_user_location(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude

    await state.update_data(user_lat=lat, user_lon=lon)

    await show_nearby_page(message, lat, lon, page=1)


async def show_nearby_page(message: types.Message, lat, lon, page=1):
    data = api.get_nearby_stadiums(lat, lon, page)

    if not data:
        await message.answer("Yaqin atrofda maydonlar topilmadi.")
        return

    if isinstance(data, dict) and 'results' in data:
        stadiums = data['results']
        has_next = data.get('next')
    elif isinstance(data, list):
        stadiums = data
        has_next = False
    else:
        await message.answer("Ma'lumotlar formatida xatolik.")
        return

    if not stadiums:
        await message.answer("Yaqin atrofda maydonlar topilmadi.")
        return

    try:
        st = stadiums[0] if isinstance(data, dict) else stadiums[page - 1]
    except IndexError:
        await message.answer("Boshqa maydon topilmadi.")
        return

    dist = st.get('distance', 0)
    caption = (
        f"🏟 <b>{st['name']}</b>\n"
        f"📏 Masofa: <b>{dist:.2f} km</b>\n"
        f"📍 Manzil: {st['address']}\n"
        f"💰 Narxi: {float(st['price_per_hour']):,.0f} so'm".replace(",", " ")
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️ Batafsil", callback_data=f"det_{st['id']}")
    kb.button(text="⚡️ Bron qilish", callback_data=f"b_{st['id']}")

    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"near_{page - 1}"))

    if has_next or (isinstance(data, list) and len(data) > page):
        nav_buttons.append(types.InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"near_{page + 1}"))

    if nav_buttons:
        kb.row(*nav_buttons)

        img_url = st.get('image')

        try:
            if img_url and "127.0.0.1" not in img_url and not img_url.endswith('.html'):
                await message.answer_photo(
                    photo=img_url,
                    caption=caption,
                    reply_markup=kb.as_markup(),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    text=f"🖼 <i>(Rasm yuklanmadi)</i>\n\n{caption}",
                    reply_markup=kb.as_markup(),
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Rasm yuklashda xatolik: {e}")
            await message.answer(
                text=caption,
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )


@router.callback_query(F.data.startswith("near_"))
async def paginate_nearby(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    user_data = await state.get_data()

    lat = user_data.get('user_lat')
    lon = user_data.get('user_lon')

    if not lat or not lon:
        await callback.answer("Lokatsiya ma'lumotlari eskirgan. Iltimos, qayta yuboring.", show_alert=True)
        return

    await callback.message.delete()
    await show_nearby_page(callback.message, lat, lon, page)
    await callback.answer()


@router.callback_query(F.data.startswith("b_"))
async def start_booking(callback: types.CallbackQuery):
    stadium_id = callback.data.split("_")[1]

    await callback.message.edit_text(
        "📅 Bron qilish uchun sana tanlang (1 oylik muddat):",
        reply_markup=get_days_keyboard(stadium_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bookday_"))
async def show_time_slots(callback: types.CallbackQuery, state: FSMContext):
    _, stadium_id, selected_date = callback.data.split("_")

    st = api.get_stadium_detail(stadium_id)
    if not st:
        await callback.answer("Xatolik yuz berdi")
        return

    start_h = int(st.get('open_at', '08:00').split(':')[0])
    end_h = int(st.get('closed_at', '22:00').split(':')[0])

    booked_slots = st.get('booked_slots', [])

    await callback.message.edit_text(
        f"🏟 <b>{st['name']}</b>\n📅 Sana: {selected_date}\n\nKerakli vaqt oralig'ini tanlang:",
        reply_markup=get_slots_keyboard(stadium_id, selected_date, start_h, end_h, booked_slots),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("save_"))
async def confirm_time_slot(callback: types.CallbackQuery, state: FSMContext):
    _, stadium_id, date, time = callback.data.split("_")

    await state.update_data(
        stadium_id=stadium_id,
        booking_date=date,
        start_time=time
    )

    h = int(time.split(":")[0])
    end_time = f"{h + 1:02d}:00"
    await state.update_data(end_time=end_time)

    text = (
        f"🏁 <b>Bronni tasdiqlang:</b>\n"
        f"📅 Sana: {date}\n"
        f"⏰ Vaqt: {time} - {end_time}\n"
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data="final_confirm")
    kb.button(text="❌ Bekor qilish", callback_data=f"bookday_{stadium_id}_{date}")

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "final_confirm")
async def final_booking_confirmation(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    stadium_id = data.get("stadium_id")
    booking_date = data.get("booking_date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    success_text = (
        "✅ <b>Muvaffaqiyatli band qilindi!</b>\n\n"
        f"🏟 Stadion ID: {stadium_id}\n"
        f"📅 Sana: {booking_date}\n"
        f"⏰ Vaqt: {start_time} - {end_time}\n\n"
        "Operatorimiz tez orada siz bilan bog'lanadi."
    )

    await callback.message.edit_text(success_text, parse_mode="HTML")

    await state.clear()
    await callback.answer("Bron tasdiqlandi!")
