## Установи модуль ping3, выполнив в терминале:
pip install ping3
pip3 install ping3

mkdir -p solana_python_bot
cd solana_python_bot && nano config.json
nano solana_monitor_bot.py

## Создадим systemd-сервис и таймер
```bash
sudo tee /etc/systemd/system/solana-monitor.service > /dev/null <<EOF
[Unit]
Description=Solana Validator Monitor Bot
After=network-online.target

[Service]
Type=oneshot
ExecStart=/root/myevn/bin/python /root/solana_python_bot/solana_monitor_bot.py
StandardOutput=append:/var/log/solana_monitor.log
StandardError=append:/var/log/solana_monitor.log
EOF
```

## Создадим systemd-таймер и таймер
```bash
sudo tee /etc/systemd/system/solana-monitor.timer > /dev/null <<EOF
[Unit]
Description=Run Solana Monitor every 1 minute

[Timer]
OnBootSec=1min
OnUnitActiveSec=60s
Unit=solana-monitor.service

[Install]
WantedBy=timers.target
EOF
```

## ✅ 3. Установка и запуск
```bash
systemctl daemon-reexec &&
systemctl daemon-reload &&
systemctl enable --now solana-monitor.timer
```
## Проверить статус таймера и сервиса:
```bash
systemctl list-timers --all | grep solana
systemctl status solana-monitor.service
```

## ✅ Поддержка ротации логов через logrotate
```bash
sudo tee /etc/logrotate.d/solana_monitor > /dev/null <<EOF
/var/log/solana_monitor.log {
    daily
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
```

## Тестировать вручную:
```bash
sudo logrotate -f /etc/logrotate.d/solana_monitor
```

## Каждый запуск скрипта будет логироваться в /var/log/solana_monitor.log.
```bash
tail -f /var/log/solana_monitor.log
```

## Или запустит через cron
```bash
*/5 * * * * /root/myevn/bin/python /root/solana_python_bot/solana_monitor_bot.py >> $HOME/solana_python_bot/cron.log 2>&1
59 23 * * * rm $HOME/solana_python_bot/cron.log
```