# Nutrition Bot

Telegram-бот на базе [aiogram 3](https://docs.aiogram.dev/) для учёта питания и подсчёта КБЖУ. Бот ведёт анкету пользователя, запоминает типичные блюда и считает дневные итоги с подсказками.

## Возможности

- регистрация с анкетой (пол, возраст, рост, вес, цель, активность);
- расчёт нормы по формуле Mifflin-St Jeor с подсветкой 🟢/🟡/🔴;
- добавление блюд по тексту, автоматическое использование шаблонов;
- сохранение данных в SQLite;
- ручные и автоматические итоги дня с коротким советом;
- заготовка для подключения LLM (system_prompt и `services.llm_client`).

## Структура

```
nutrition_bot/
├─ __main__.py
├─ config.py
├─ keyboards.py
├─ handlers/
│   ├─ start.py
│   ├─ food.py
│   ├─ summary.py
│   └─ help.py
├─ services/
│   ├─ user_service.py
│   ├─ food_service.py
│   ├─ templates.py
│   ├─ calc.py
│   ├─ llm_client.py
│   └─ scheduler.py
├─ fatsecret_client.py
├─ product_db.py
└─ storage/
    └─ db.py
```

`system_prompt.txt` лежит рядом и подгружается из `config.py`.

## Запуск

1. Создайте и активируйте виртуальное окружение.
2. Установите зависимости:

   ```bash
   pip install -e .
   ```

3. Создайте файл `.env` в корне проекта и добавьте туда ключи:

   ```env
   BOT_TOKEN=токен_бота
   OPENAI_API_KEY=опционально_для_llm
   FATSECRET_KEY=client_id
   FATSECRET_SECRET=client_secret
   TZ=Europe/Moscow
   ```

4. Запустите бота командой:

   ```bash
   python -m nutrition_bot
   ```

SQLite-база создаётся автоматически в `src/nutrition_bot/nutrition_bot.db`.

## Тесты

```
pytest
```

## Деплой на VDS (Ubuntu)

Ниже пример пошагового деплоя на сервере:

```bash
git clone <repo_url> mnyam_mniam_bot
cd mnyam_mniam_bot
git checkout codex/-telegram

python3.10 -m venv venv
source venv/bin/activate
pip install -e .

cat <<'EOF' > .env
BOT_TOKEN=...
FATSECRET_KEY=...
FATSECRET_SECRET=...
TZ=Europe/Moscow
# при необходимости добавьте OPENAI_API_KEY и OPENAI_MODEL
EOF

python3.10 -m nutrition_bot
```

Для автозапуска через `systemd` можно использовать шаблон unit-файла:

```ini
[Unit]
Description=Nutrition Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/mnyam_mniam_bot
EnvironmentFile=/opt/mnyam_mniam_bot/.env
ExecStart=/opt/mnyam_mniam_bot/venv/bin/python -m nutrition_bot
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Сохраните файл, например, как `/etc/systemd/system/nutrition-bot.service`, затем выполните:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nutrition-bot.service
```
