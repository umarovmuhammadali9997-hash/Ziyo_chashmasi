import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import database as db
from config import BOT_TOKEN, BRAND_NAME, ADMIN_IDS
from subjects import SUBJECTS, DIRECTION_SUBJECTS

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

BOT_USERNAME = ""  # main() da to'ldiriladi

# ============================================================
#  /start xabari — bu matnni keyin xohlaganingizcha o'zgartiring
# ============================================================
START_TEXT = (
    f"Assalomu alaykum! \"{BRAND_NAME}\" test botiga xush kelibsiz. 👋\n\n"
    "..."  # <-- bu yerga to'liq tanishtiruv matnini yozasiz
    "\n\nBotdan foydalanish uchun avval ro'yxatdan o'ting."
)


# ============================================================
#  Registratsiya bosqichlari
# ============================================================
class Reg(StatesGroup):
    name = State()
    grade = State()
    phone = State()
    direction = State()


class Answer(StatesGroup):
    waiting = State()


class AddTest(StatesGroup):
    title = State()
    pdf = State()
    answers = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


GRADES = ["8-sinf", "9-sinf", "10-sinf", "11-sinf", "Abituriyent", "O'qituvchi"]

DIRECTIONS = [
    "Tibbiyot yo'nalishi",
    "Aniq fanlar (matematika, ingliz tili)",
    "Yuridika",
    "Filologiya",
]


def grades_kb() -> InlineKeyboardMarkup:
    rows, row = [], []
    for i, g in enumerate(GRADES):
        row.append(InlineKeyboardButton(text=g, callback_data=f"grade:{i}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def directions_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=d, callback_data=f"dir:{i}")]
        for i, d in enumerate(DIRECTIONS)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def subjects_kb(direction: str) -> InlineKeyboardMarkup:
    keys = DIRECTION_SUBJECTS.get(direction, [])
    rows = [
        [InlineKeyboardButton(text=SUBJECTS[k], callback_data=f"subj:{k}")]
        for k in keys
    ]
    rows.append([InlineKeyboardButton(text="👥 Do'st taklif qilish", callback_data="referral")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_main_menu(message: Message, direction: str):
    await message.answer(
        f"📚 Yo'nalishingiz: {direction}\n\nFanni tanlang:",
        reply_markup=subjects_kb(direction),
    )


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# ---------- /start ----------
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, command: CommandObject):
    await state.clear()
    if db.is_registered(message.from_user.id):
        user = db.get_user(message.from_user.id)
        await message.answer(
            f"Xush kelibsiz qaytadan, {user['full_name']}! ✅",
            reply_markup=ReplyKeyboardRemove(),
        )
        await show_main_menu(message, user["direction"])
        return

    # Referal havolasi: ?start=ref<id>
    payload = command.args or ""
    if payload.startswith("ref"):
        ref_part = payload[3:]
        if ref_part.isdigit() and int(ref_part) != message.from_user.id:
            await state.update_data(referrer_id=int(ref_part))

    await message.answer(START_TEXT, reply_markup=ReplyKeyboardRemove())
    await message.answer("1️⃣ Ism va familiyangizni yozing:")
    await state.set_state(Reg.name)


# ---------- 1. Ism familiya ----------
@dp.message(Reg.name, F.text)
async def reg_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 3:
        await message.answer("Iltimos, to'liq ism va familiyangizni yozing.")
        return
    await state.update_data(full_name=name)
    await message.answer("2️⃣ Qaysi sinfda o'qiysiz?", reply_markup=grades_kb())
    await state.set_state(Reg.grade)


# ---------- 2. Sinf ----------
@dp.callback_query(Reg.grade, F.data.startswith("grade:"))
async def reg_grade(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])
    await state.update_data(grade=GRADES[idx])
    await call.message.edit_text(f"Sinf: {GRADES[idx]} ✅")
    await call.message.answer(
        "3️⃣ Telefon raqamingizni yuboring.\n"
        "Pastdagi tugmani bosing 👇",
        reply_markup=phone_kb(),
    )
    await state.set_state(Reg.phone)
    await call.answer()


# ---------- 3. Telefon (kontakt yoki matn) ----------
@dp.message(Reg.phone, F.contact)
async def reg_phone_contact(message: Message, state: FSMContext):
    await _save_phone(message, state, message.contact.phone_number)


@dp.message(Reg.phone)
async def reg_phone_invalid(message: Message, state: FSMContext):
    await message.answer(
        "Iltimos, pastdagi \"📱 Telefon raqamni yuborish\" tugmasini bosing.\n"
        "Raqamni qo'lda yozish mumkin emas.",
        reply_markup=phone_kb(),
    )


async def _save_phone(message: Message, state: FSMContext, phone: str):
    await state.update_data(phone=phone)
    await message.answer("Telefon qabul qilindi ✅", reply_markup=ReplyKeyboardRemove())
    await message.answer("4️⃣ Yo'nalishni tanlang:", reply_markup=directions_kb())
    await state.set_state(Reg.direction)


# ---------- 4. Yo'nalish ----------
@dp.callback_query(Reg.direction, F.data.startswith("dir:"))
async def reg_direction(call: CallbackQuery, state: FSMContext):
    idx = int(call.data.split(":")[1])
    direction = DIRECTIONS[idx]
    data = await state.get_data()

    db.register_user(
        user_id=call.from_user.id,
        username=call.from_user.username,
        full_name=data["full_name"],
        grade=data["grade"],
        phone=data["phone"],
        direction=direction,
    )

    # Referal bonusi (agar havola orqali kelgan bo'lsa)
    referrer_id = data.get("referrer_id")
    if referrer_id and db.is_registered(referrer_id):
        if db.add_referral(referrer_id, call.from_user.id):
            stats = db.referral_stats(referrer_id)
            try:
                await bot.send_message(
                    referrer_id,
                    f"🎉 Sizning havolangiz orqali yangi do'st qo'shildi: {data['full_name']}\n"
                    f"💰 Balansingiz: {stats['balance']} | 👥 Takliflar: {stats['ref_count']}",
                )
            except Exception:
                pass

    await state.clear()

    await call.message.edit_text(f"Yo'nalish: {direction} ✅")
    await call.message.answer(
        "🎉 Ro'yxatdan o'tish tugadi!\n\n"
        f"👤 {data['full_name']}\n"
        f"🎓 {data['grade']}\n"
        f"📞 {data['phone']}\n"
        f"🧭 {direction}"
    )
    await show_main_menu(call.message, direction)
    await call.answer()


# ============================================================
#  Fan tanlandi -> testlar ro'yxati (bazadan)
# ============================================================
@dp.callback_query(F.data.startswith("subj:"))
async def on_subject(call: CallbackQuery):
    key = call.data.split(":", 1)[1]
    tests = db.list_tests_db(key)
    if not tests:
        await call.answer("Bu fanga hozircha test qo'shilmagan.", show_alert=True)
        return
    rows = [
        [InlineKeyboardButton(text=f"📄 {t['title']}", callback_data=f"test:{t['id']}")]
        for t in tests
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await call.message.answer(f"{SUBJECTS.get(key, key)} — testni tanlang:", reply_markup=kb)
    await call.answer()


# ============================================================
#  Test tanlandi -> PDF + javob yuborish ma'lumoti + tayyorman tugmasi
# ============================================================
@dp.callback_query(F.data.startswith("test:"))
async def on_test(call: CallbackQuery):
    test_id = int(call.data.split(":", 1)[1])
    test = db.get_test_db(test_id)
    if not test:
        await call.answer("Test topilmadi.", show_alert=True)
        return

    await call.message.answer_document(
        test["file_id"],
        caption=f"📄 {test['title']}\n{BRAND_NAME}",
    )

    n = len(test["answers"])
    info = (
        "📝 Testni yeching va javoblaringizni shu formatda yuboring:\n\n"
        "• <code>1a 2b 3c ...</code>\n"
        "• yoki faqat harflar: <code>abcd...</code>\n\n"
        f"Jami {n} ta savol. Tayyor bo'lsangiz, pastdagi tugmani bosing 👇"
    )
    ready_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Kalit yuborishga tayyorman",
                              callback_data=f"ready:{test_id}")]
    ])
    await call.message.answer(info, parse_mode="HTML", reply_markup=ready_kb)
    await call.answer()


# ============================================================
#  "Tayyorman" -> javob kutish rejimi
# ============================================================
@dp.callback_query(F.data.startswith("ready:"))
async def on_ready(call: CallbackQuery, state: FSMContext):
    test_id = int(call.data.split(":", 1)[1])
    test = db.get_test_db(test_id)
    if not test:
        await call.answer("Test topilmadi.", show_alert=True)
        return
    db.set_active_test(call.from_user.id, test["subject"], list(test["answers"]))
    await state.update_data(test_title=test["title"])
    await state.set_state(Answer.waiting)
    await call.message.answer(
        f"✍️ Endi javoblaringizni yuboring ({len(test['answers'])} ta savol):"
    )
    await call.answer()


# ============================================================
#  Javoblarni tekshirish
# ============================================================
def parse_answers(text: str):
    """Matndan a/b/c/d harflarini tartib bo'yicha ajratib oladi."""
    return [ch.lower() for ch in text if ch.lower() in "abcd"]


@dp.message(Answer.waiting, F.text)
async def check_answers(message: Message, state: FSMContext):
    active = db.get_active_test(message.from_user.id)
    if not active:
        await state.clear()
        await message.answer("Faol test topilmadi. /start bosing.")
        return

    key = active["answer_key"]            # to'g'ri javoblar
    n = len(key)
    user_ans = parse_answers(message.text)

    if len(user_ans) < n:
        await message.answer(
            f"⚠️ Siz {len(user_ans)} ta javob yubordingiz, lekin testda {n} ta savol bor.\n"
            "Iltimos, hammasini to'liq yuboring."
        )
        return
    user_ans = user_ans[:n]

    correct = 0
    wrong_lines = []
    for i in range(n):
        if user_ans[i] == key[i]:
            correct += 1
        else:
            wrong_lines.append(f"{i+1}-savol: siz {user_ans[i].upper()} ❌  to'g'ri: {key[i].upper()}")

    wrong = n - correct
    percent = round(correct / n * 100)

    data = await state.get_data()
    title = data.get("test_title", "Test")

    text = [f"📊 <b>{title}</b> natijasi:\n"]
    text.append(f"✅ To'g'ri: <b>{correct}</b> ta")
    text.append(f"❌ Xato: <b>{wrong}</b> ta\n")
    if wrong_lines:
        text.append("<b>Xato javoblar:</b>")
        text.extend(wrong_lines)
        text.append("")
    text.append(f"🏆 Ball: <b>{correct}/{n}</b> ({percent}%)")

    db.save_result(message.from_user.id, active["subject"], correct, n, "".join(user_ans))
    db.clear_active_test(message.from_user.id)
    await state.clear()

    await message.answer("\n".join(text), parse_mode="HTML")


# ============================================================
#  Referal: havola + statistika
# ============================================================
async def show_referral(message: Message, user_id: int):
    if not db.is_registered(user_id):
        await message.answer("Avval ro'yxatdan o'ting: /start")
        return
    stats = db.referral_stats(user_id)
    link = f"https://t.me/{BOT_USERNAME}?start=ref{user_id}"
    await message.answer(
        "👥 <b>Referal dasturi</b>\n\n"
        "Quyidagi havolani do'stlaringizga ulashing. Ular shu havola orqali kirib "
        "ro'yxatdan o'tsa, sizga bonus qo'shiladi.\n\n"
        f"🔗 {link}\n\n"
        f"👥 Takliflaringiz: <b>{stats['ref_count']}</b>\n"
        f"💰 Balansingiz: <b>{stats['balance']}</b>",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@dp.callback_query(F.data == "referral")
async def on_referral(call: CallbackQuery):
    await show_referral(call.message, call.from_user.id)
    await call.answer()


@dp.message(Command("referal"))
async def cmd_referral(message: Message):
    await show_referral(message, message.from_user.id)


# ============================================================
#  ADMIN PANEL
# ============================================================
def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Test qo'shish", callback_data="adm:add")],
        [InlineKeyboardButton(text="🗑 Test o'chirish", callback_data="adm:del")],
        [InlineKeyboardButton(text="📋 Testlar ro'yxati", callback_data="adm:list")],
    ])


def admin_subjects_kb(prefix: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"{prefix}:{key}")]
        for key, name in SUBJECTS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return  # admin bo'lmaganlarga javob yo'q
    await state.clear()
    await message.answer("🛠 Admin panel", reply_markup=admin_menu_kb())


# ---------- Test qo'shish ----------
@dp.callback_query(F.data == "adm:add")
async def adm_add(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.message.answer("Qaysi fanga test qo'shasiz?",
                              reply_markup=admin_subjects_kb("addsub"))
    await call.answer()


@dp.callback_query(F.data.startswith("addsub:"))
async def adm_add_subject(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    key = call.data.split(":", 1)[1]
    await state.update_data(subject=key)
    await state.set_state(AddTest.title)
    await call.message.answer(
        f"Fan: {SUBJECTS[key]}\n\n📝 Test nomini yozing (masalan: DTM Ziyo chashmasi 002):"
    )
    await call.answer()


@dp.message(AddTest.title, F.text)
async def adm_add_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddTest.pdf)
    await message.answer("📎 Endi test PDF faylini yuboring:")


@dp.message(AddTest.pdf, F.document)
async def adm_add_pdf(message: Message, state: FSMContext):
    await state.update_data(file_id=message.document.file_id)
    await state.set_state(AddTest.answers)
    await message.answer(
        "✅ PDF qabul qilindi.\n\n"
        "🔑 Endi to'g'ri javoblar kalitini yuboring (masalan: <code>abcdabcd...</code>):",
        parse_mode="HTML",
    )


@dp.message(AddTest.pdf)
async def adm_add_pdf_invalid(message: Message):
    await message.answer("Iltimos, PDF faylni yuboring.")


@dp.message(AddTest.answers, F.text)
async def adm_add_answers(message: Message, state: FSMContext):
    answers = "".join(parse_answers(message.text))
    if not answers:
        await message.answer("Kalit bo'sh yoki noto'g'ri. Faqat a/b/c/d harflari bilan yuboring.")
        return
    data = await state.get_data()
    db.add_test(data["subject"], data["title"], data["file_id"], answers)
    await state.clear()
    await message.answer(
        f"✅ Test qo'shildi!\n\n"
        f"📚 Fan: {SUBJECTS[data['subject']]}\n"
        f"📄 Nomi: {data['title']}\n"
        f"🔢 Savollar soni: {len(answers)}",
        reply_markup=admin_menu_kb(),
    )


# ---------- Test o'chirish ----------
@dp.callback_query(F.data == "adm:del")
async def adm_del(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.message.answer("Qaysi fandan o'chirasiz?",
                              reply_markup=admin_subjects_kb("delsub"))
    await call.answer()


@dp.callback_query(F.data.startswith("delsub:"))
async def adm_del_subject(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    key = call.data.split(":", 1)[1]
    tests = db.list_tests_db(key)
    if not tests:
        await call.answer("Bu fanda test yo'q.", show_alert=True)
        return
    rows = [
        [InlineKeyboardButton(text=f"🗑 {t['title']}", callback_data=f"delone:{t['id']}")]
        for t in tests
    ]
    await call.message.answer(f"{SUBJECTS[key]} — o'chirish uchun tanlang:",
                              reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


@dp.callback_query(F.data.startswith("delone:"))
async def adm_del_one(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    test_id = int(call.data.split(":", 1)[1])
    test = db.get_test_db(test_id)
    db.delete_test_db(test_id)
    title = test["title"] if test else "Test"
    await call.message.edit_text(f"🗑 O'chirildi: {title}")
    await call.answer("O'chirildi")


# ---------- Testlar ro'yxati ----------
@dp.callback_query(F.data == "adm:list")
async def adm_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    grouped = db.all_tests_grouped()
    if not grouped:
        await call.answer("Hozircha test yo'q.", show_alert=True)
        return
    lines = ["📋 <b>Barcha testlar:</b>\n"]
    for key, tests in grouped.items():
        lines.append(f"\n{SUBJECTS.get(key, key)} ({len(tests)} ta):")
        for t in tests:
            lines.append(f"  • {t['title']} — {len(t['answers'])} savol")
    await call.message.answer("\n".join(lines), parse_mode="HTML")
    await call.answer()


# ============================================================
async def main():
    global BOT_USERNAME
    db.init_db()
    me = await bot.get_me()
    BOT_USERNAME = me.username
    logging.info(f"Bot ishga tushdi: @{BOT_USERNAME}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
