# Nutrition Bot

Telegram-бот на базе [aiogram 3](https://docs.aiogram.dev/) для учёта питания и подсчёта КБЖУ. Бот ведёт анкету пользователя, запоминает типичные блюда, считает дневные итоги и может запрашивать данные у FatSecret, если оффлайн-база не знает продукт.

## Быстрый старт (Python 3.10)

```bash
git clone <repo_url> nutrition-bot
cd nutrition-bot
python3.10 -m venv venv
source venv/bin/activate
pip install -e .
```

Создайте `.env` в корне проекта:

```env
BOT_TOKEN=ваш_токен_бота
FATSECRET_KEY=client_id
FATSECRET_SECRET=client_secret
TZ=Europe/Moscow
# при необходимости добавьте OPENAI_API_KEY и OPENAI_MODEL
```

Проверьте, что импорты и конфигурация собраны корректно:

```bash
python scripts/smoke.py
```

После этого запустите бота:

```bash
python3.10 -m nutrition_bot
```

В логах появятся сообщения `Scheduler started` и `Start polling`, а в Telegram /start запустит анкету (пол → возраст → рост → вес → цель → активность).

## Основные возможности

- Анкета /start с расчётом норм по формуле Mifflin–St Jeor.
- Добавление блюд свободным текстом: `курица 150`, `салат цезарь 200` и т. п.
- Подсчёт КБЖУ по оффлайн-базе на 100 г, с фолбэком к FatSecret.
- Память шаблонов блюд и подсказки, если данных не хватает.
- Кнопки для текущих итогов и закрытия дня, автоматический отчёт в 03:00 (Europe/Moscow по умолчанию).

## Структура проекта

```
src/nutrition_bot/
├── __main__.py          # точка входа (python -m nutrition_bot)
├── config.py            # загрузка .env и системный промпт
├── data/products.json   # оффлайн-база продуктов (КБЖУ на 100 г)
├── fatsecret_client.py  # клиент FatSecret (OAuth2 client-credentials)
├── handlers/            # aiogram-хэндлеры (start, food, summary, help)
├── keyboards.py         # клавиатуры Telegram
├── product_db.py        # поиск по оффлайн-базе и кэш
├── services/            # бизнес-логика (учёт еды, расчёт норм, планировщик)
└── storage/db.py        # JSON-хранилище пользователей и записей
```

Дополнительные утилиты:

- `scripts/smoke.py` — быстрая проверка импорта и конфигурации без запуска polling.

## Деплой на сервер (пример)

```bash
sudo git clone https://github.com/kuznetsovmaximdesign/eatchatbot.git /opt/mnyam_mniam_bot
cd /opt/mnyam_mniam_bot
python3.10 -m venv venv
source venv/bin/activate
pip install -e .
cat <<'EOF' > .env
BOT_TOKEN=...
FATSECRET_KEY=...
FATSECRET_SECRET=...
TZ=Europe/Moscow
EOF
python3.10 -m nutrition_bot
```

Пример `systemd` unit-файла для автозапуска:

```ini
[Unit]
Description=Nutrition Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/mnyam_mniam_bot
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/mnyam_mniam_bot/venv/bin/python3.10 -m nutrition_bot
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Активируйте сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nutrition-bot.service
sudo systemctl status nutrition-bot.service --no-pager
```

## Тесты

```bash
pytest
```
