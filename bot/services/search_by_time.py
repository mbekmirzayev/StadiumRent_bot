from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api_client import APIClient
from bot.keyboards.inline import get_days_keyboard, get_slots_keyboard
from utils.states import SearchByTime

router = Router()
api = APIClient()


@router.message(F.text == "🔍 Vaqt bo'yicha qidirish")
async def start_search_by_time(message: types.Message, state: FSMContext):
    try:
        print("DEBUG: Tugma bosildi, holat o'rnatilmoqda...")
        await state.clear()
        await state.set_state(SearchByTime.waiting_for_date)

        kb = get_days_keyboard()  # Argumentni tekshiring!

        await message.answer(
            "📅 <b>Qaysi sana uchun bo'sh joy qidirmoqchisiz?</b>",
            reply_markup=kb,
            parse_mode="HTML"
        )
        print("DEBUG: Kalendar muvaffaqiyatli yuborildi.")

    except Exception as e:
        print(f"❌ HANDLER ICHIDA XATO: {e}")
        await message.answer("Tizimda ichki xatolik yuz berdi.")


@router.callback_query(SearchByTime.waiting_for_date, F.data.startswith("day_"))
async def search_process_day(callback: types.CallbackQuery, state: FSMContext):
    selected_date = callback.data.split("_")[1]
    await state.update_data(search_date=selected_date, search_slots=[])
    await state.set_state(SearchByTime.waiting_for_slots)

    await callback.message.edit_text(
        f"📅 Sana: {selected_date}\n\n<b>O'zingizga qulay vaqt oralig'ini tanlang:</b>",
        reply_markup=get_slots_keyboard(
            stadium_id="search",
            date_str=selected_date,
            start_h=8,
            end_h=22,
            booked_slots=[]
        ),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("tgl_search_"))
async def search_time_toggle(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    time_str = parts[2]

    user_data = await state.get_data()
    date_str = user_data.get("search_date")

    selected_slots = user_data.get("selected_slots", [])

    if time_str in selected_slots:
        selected_slots.remove(time_str)
    else:
        selected_slots.append(time_str)

    selected_slots.sort()
    await state.update_data(selected_slots=selected_slots)

    from bot.keyboards.inline import get_slots_keyboard
    await callback.message.edit_reply_markup(
        reply_markup=get_slots_keyboard(
            stadium_id="search",
            date_str=date_str,
            start_h=6,
            end_h=24,
            booked_slots=[],
            selected_slots=selected_slots
        )
    )
    await callback.answer()


@router.callback_query(SearchByTime.waiting_for_slots, F.data.startswith("conf_bk_"))
async def perform_search(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    slots = data.get("search_slots", [])  #  ["18:00", "19:00"]
    date = data.get("search_date")  #  "2026-03-14"

    if not slots:
        return await callback.answer("Iltimos, vaqt tanlang!", show_alert=True)

    start_t = slots[0]

    last_slot_hour = int(slots[-1].split(":")[0])
    end_t = f"{last_slot_hour + 1:02d}:00"  # "20:00"

    stadiums = api.search_by_time(date=date, start_time=start_t, end_time=end_t)

    if not stadiums:
        await callback.message.answer("😕 Afsus, bu vaqtda bo'sh stadionlar topilmadi.")
    else:
        await callback.message.answer(f"✅ <b>{len(stadiums)} ta bo'sh stadion topildi:</b>", parse_mode="HTML")

        for st in stadiums:
            builder = InlineKeyboardBuilder()
            builder.button(text="⚡️ Band qilish", callback_data=f"st_book_{st['id']}")

            price = "{:,.0f}".format(st['price']).replace(",", " ")

            await callback.message.answer(
                f"🏟 <b>{st['name']}</b>\n"
                f"📍 Manzil: {st['address']}\n"
                f"💰 Narxi: {price} so'm/soat",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )

    await state.clear()


@router.callback_query(F.data == "cnf_bk_search")
async def process_search_confirm(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    selected_slots = user_data.get("selected_slots", [])
    search_date = user_data.get("search_date")

    if not selected_slots:
        await callback.answer("Iltimos, kamida bitta vaqt oralig'ini tanlang!", show_alert=True)
        return

    await callback.message.edit_text("🔍 Tanlangan vaqt bo'yicha bo'sh stadionlar qidirilmoqda...")

    try:
        available_stadiums = api.search_by_time(
            date=search_date,
            slots=selected_slots
        )

        if not available_stadiums:
            await callback.message.answer(
                f"😔 Afsuski, {search_date} kuni tanlangan vaqtda bo'sh stadionlar topilmadi.\n"
                "Boshqa vaqtni tanlab ko'ring."
            )
            return

        response_text = f"✅ {search_date} kuni uchun topilgan stadionlar:\n\n"

        for st in available_stadiums:
            response_text += (
                f"🏟 <b>{st['name']}</b>\n"
                f"💰 Narxi: {st['price']} so'm/soat\n"
                f"📍 Manzil: {st['address']}\n"
                f"👉 /stadium_{st['id']}\n\n"
            )

        await callback.message.answer(response_text, parse_mode="HTML")

    except Exception as e:
        await callback.message.answer(f"❌ Qidiruvda xatolik yuz berdi: {str(e)}")
