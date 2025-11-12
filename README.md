# Nutrition Bot


cat <<'EOF' > .env
BOT_TOKEN=...
FATSECRET_KEY=...
FATSECRET_SECRET=...
TZ=Europe/Moscow


```ini
[Unit]
Description=Nutrition Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/mnyam_mniam_bot


[Install]
WantedBy=multi-user.target
```



```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nutrition-bot.service

