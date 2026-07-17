# Вставка секретов бота на сервер Beget по SSH.
# Токен/ключ вводятся здесь и уходят сразу на сервер — в чат их слать не нужно.
$ErrorActionPreference = "Stop"
$key = "$env:USERPROFILE\.ssh\beget_bot"
$srv = "root@45.146.167.152"

Write-Host "=== Настройка секретов Telegram-бота ===" -ForegroundColor Cyan
Write-Host ""

$tok = Read-Host "1) Вставьте токен от @BotFather (Enter — пропустить)"
if ($tok.Trim()) {
    $t = $tok.Trim()
    ssh -i $key $srv "sed -i 's|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$t|' /home/bot/tgbot/.env"
    Write-Host "   Токен записан на сервер." -ForegroundColor Green
}

$api = Read-Host "2) Вставьте API-ключ Anthropic (Enter — пропустить, если ещё нет)"
if ($api.Trim()) {
    $a = $api.Trim()
    ssh -i $key $srv "sed -i 's|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$a|' /home/bot/tgbot/.env"
    Write-Host "   API-ключ записан на сервер." -ForegroundColor Green
}

Write-Host ""
Write-Host "Перезапускаю бота..." -ForegroundColor Cyan
ssh -i $key $srv "systemctl restart tgbot; sleep 3; systemctl is-active tgbot"
Write-Host ""
Write-Host "Готово. Если выше написано 'active' - бот запущен." -ForegroundColor Green
Write-Host "Теперь напишите своему боту /start в Telegram (первым!)."
Read-Host "Enter - закрыть окно"
