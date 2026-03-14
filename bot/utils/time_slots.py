from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext

from api_client import APIClient
from bot.keyboards.inline import get_slots_keyboard
from utils.states import SearchByTime

router = Router()
api = APIClient()


@router.callback_query(F.data.startswith("day_"))
async def process_day_selection(callback: types.CallbackQuery, state: FSMContext):
    selected_date = callback.data.split("_")[1]
    user_data = await state.get_data()
    stadium_id = user_data.get("stadium_id")

    if not stadium_id or stadium_id == "search":
        await state.update_data(search_date=selected_date, stadium_id="search")

        start_h, end_h = 6, 24
        booked_slots = []

        await callback.message.edit_text(
            f"📅 Sana: {selected_date}\n\n<b>Qidiruv uchun vaqt oralig'ini tanlang:</b>",
            reply_markup=get_slots_keyboard("search", selected_date, start_h, end_h, booked_slots),
            parse_mode="HTML"
        )
        await state.set_state(SearchByTime.waiting_for_slots)
        return

    await state.update_data(booking_date=selected_date)
    stadium = api.get_stadium_detail(stadium_id)

    if not stadium:
        await callback.answer("Stadion ma'lumotlarini olib bo'lmadi.")
        return

    start_time_raw = stadium.get('open_at') or stadium.get('start_time') or '08:00'
    end_time_raw = stadium.get('closed_at') or stadium.get('end_time') or '22:00'

    start_h = int(start_time_raw.split(':')[0])
    end_h = int(end_time_raw.split(':')[0])
    booked_slots = stadium.get('booked_slots', [])

    await callback.message.edit_text(
        f"🏟 {stadium.get('name')}\n📅 Sana: {selected_date}\n\n<b>Kerakli vaqt slotini tanlang:</b>",
        reply_markup=get_slots_keyboard(stadium_id, selected_date, start_h, end_h, booked_slots),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("tgl_"))
async def process_time_toggle(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    stadium_id = parts[1]
    time_str = parts[2]

    user_data = await state.get_data()
    date_str = user_data.get("booking_date") or user_data.get("search_date")

    selected_slots = user_data.get("selected_slots", [])

    if time_str in selected_slots:
        selected_slots.remove(time_str)
    else:
        selected_slots.append(time_str)

    await state.update_data(selected_slots=selected_slots)

    start_h = user_data.get('start_h', 8)
    end_h = user_data.get('end_h', 22)
    booked_slots = user_data.get('booked_slots', [])

    await callback.message.edit_reply_markup(
        reply_markup=get_slots_keyboard(
            stadium_id=stadium_id,
            date_str=date_str,
            start_h=start_h,
            end_h=end_h,
            booked_slots=booked_slots,
            selected_slots=selected_slots
        )
    )
    await callback.answer()
