$ErrorActionPreference = "Stop"
$key = "$env:USERPROFILE\.ssh\beget_bot"
$srv = "root@45.146.167.152"
$envfile = "/home/bot/tgbot/.env"

function Set-Secret($name, $value) {
    ssh -i $key $srv "sed -i '/^$name=/d' $envfile && echo '$name=$value' >> $envfile"
    Write-Host "   $name записан на сервер." -ForegroundColor Green
}

Write-Host "=== Настройка секретов Telegram-бота ===" -ForegroundColor Cyan
Write-Host "(любой вопрос можно пропустить, нажав Enter)" -ForegroundColor DarkGray
Write-Host ""

$tok = Read-Host "1) Токен от @BotFather"
if ($tok.Trim()) { Set-Secret "TELEGRAM_BOT_TOKEN" $tok.Trim() }

$oat = Read-Host "2) Токен подписки (из команды claude setup-token, начинается с sk-ant-oat)"
if ($oat.Trim()) { Set-Secret "CLAUDE_CODE_OAUTH_TOKEN" $oat.Trim() }

$api = Read-Host "3) API-ключ Anthropic (если решили работать по API)"
if ($api.Trim()) { Set-Secret "ANTHROPIC_API_KEY" $api.Trim() }

Write-Host ""
Write-Host "Перезапускаю бота..." -ForegroundColor Cyan
ssh -i $key $srv "systemctl restart tgbot; sleep 3; systemctl is-active tgbot"
Write-Host ""
Write-Host "Готово. Если выше написано 'active' - бот запущен." -ForegroundColor Green
Read-Host "Enter - закрыть окно"
