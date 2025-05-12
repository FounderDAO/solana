#!/bin/bash

sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 12h
findtime = 300
maxretry = 2
ignoreip = 127.0.0.1 82.215.100.136

# Умное увеличение времени бана
bantime.increment = true
bantime.rndtime = 15m
bantime.maxtime = 10d
bantime.factor = 2

# Стандартный jail для SSH
[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
maxretry = 3
findtime = 300
bantime = 24h
mode = aggressive

# Кастомный jail для всех странных SSH-подключений
[sshd-banner]
enabled = true
port = ssh
filter = sshd-banner
logpath = %(sshd_log)s
maxretry = 1
bantime = 24h
findtime = 60

# Jail для повторных атак с разных jail'ов
[recidive]
enabled = true
logpath = /var/log/fail2ban.log
bantime = 7d   # навсегда
findtime = 1d
maxretry = 5
EOF


sudo tee /etc/fail2ban/filter.d/sshd-banner.conf > /dev/null <<EOF
[Definition]
failregex = 
    .*sshd.*Received disconnect from <HOST>: 3:.*banner exchange.*
    .*sshd.*Connection closed by <HOST>.*\[preauth\]
    .*sshd.*Connection reset by <HOST>.*\[preauth\]
    .*sshd.*Did not receive identification string from <HOST>
    .*sshd.*no matching key exchange found from <HOST>

ignoreregex =
EOF

sudo fail2ban-client reload && sudo systemctl restart fail2ban && sudo fail2ban-client status