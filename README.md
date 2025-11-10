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
├─ main.py
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

3. Экспортируйте токены и запустите бота:

   ```bash
   export BOT_TOKEN="<ваш_токен>"
   export LLM_API_KEY="<опционально>"
   python -m nutrition_bot.main
   ```

SQLite база создаётся автоматически в `src/nutrition_bot/nutrition_bot.db`.

## Тесты

```
pytest
```

## Скачивание архива проекта

Готовый архив со всем содержимым лежит в корне репозитория: `nutrition_bot.zip`.
Чтобы получить его локально, выполните один из вариантов:

1. Клонируйте репозиторий и скопируйте файл из корня проекта:

   ```bash
   git clone <url_репозитория>
   cd eatchatbot
   cp nutrition_bot.zip ~/Downloads/
   ```

2. Соберите свежий архив на сервере и скачайте его. В репозитории есть скрипт
   `scripts/create_archive.py`, который проходит по исходникам и собирает ZIP без
   временных файлов. Запустите его и затем скачайте получившийся файл удобным
   способом:

   ```bash
   # собрать архив из корня проекта
   python scripts/create_archive.py --output /tmp/nutrition_bot.zip

   # локально скачать через простой HTTP-сервер
   python -m http.server 8000  # запустите в каталоге, где лежит архив
   ```

   После запуска HTTP-сервера можно открыть браузер и перейти на `http://<ip>:8000`
   либо выполнить на локальной машине:

   ```bash
   curl -O http://<ip>:8000/nutrition_bot.zip
   ```

3. Если нужен только архив без дополнительной сборки, можно скачать его напрямую
   по ссылке на сырой файл GitHub:

   ```bash
   curl -L "https://raw.githubusercontent.com/<owner>/<repo>/<branch>/nutrition_bot.zip" \
     -o nutrition_bot.zip
   ```

   Замените `<owner>`, `<repo>` и `<branch>` на значения вашего репозитория.

После скачивания распакуйте архив стандартным инструментом (`unzip nutrition_bot.zip`).
