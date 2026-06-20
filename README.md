# Fergana school — Test Bot

DTM/imtihon tayyorlash uchun Telegram bot. PDF testlar + javob tekshirish + referal tizim.

## Imkoniyatlari (hozirgi holat)
- Ro'yxatdan o'tish: ism, sinf, telefon (kontakt), yo'nalish
- Yo'nalishga mos fanlar menyusi
- PDF testlar ro'yxati va yuborish
- Javoblarni tekshirish: to'g'ri/xato soni, xato javoblar, ball
- Referal tizim (havola + bonus)

## Railway'ga yuklash

1. **GitHub'ga yuklang** — barcha fayllarni o'z repozitoriyangizga push qiling.
2. **Railway'da yangi loyiha** → "Deploy from GitHub repo" → shu repo'ni tanlang.
3. **Variables** bo'limiga quyidagilarni qo'shing:
   - `BOT_TOKEN` — BotFather'dan olingan token
   - `ADMIN_IDS` — sizning Telegram ID (masalan: 123456789)
   - `BRAND_NAME` — Fergana school
4. **Volume qo'shing** (baza saqlanishi uchun):
   - Service → Settings → Volumes → New Volume
   - Mount path: `/data`
   - (Railway `RAILWAY_VOLUME_MOUNT_PATH` o'zgaruvchisini avtomatik o'rnatadi — qo'lda qo'shish shart emas)
5. Deploy avtomatik boshlanadi. Loglardan `Bot ishga tushdi: @username` chiqsa — tayyor.

## Test qo'shish
- PDF faylni `tests/<fan>/` papkasiga qo'ying (masalan `tests/biology/`)
- `tests/<fan>/index.json` ga qator qo'shing:
```json
{
  "id": "DTM_Ziyo_chashmasi002",
  "title": "DTM Ziyo chashmasi 002",
  "file": "DTM_Ziyo_chashmasi002.pdf",
  "answers": "abcdabcd..."
}
```
- `answers` — to'g'ri javoblar ketma-ketligi (savol soni = harf soni)
