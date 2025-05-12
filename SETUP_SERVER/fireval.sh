#!/bin/bash
sudo ufw allow 8000:8020/tcp &&
sudo ufw allow 8000:8020/udp && 
sudo ufw allow 11228,11229/udp &&
sudo ufw allow 2283 && 
ufw deny out from any to 10.0.0.0/8 &&
ufw deny out from any to 172.16.0.0/12 &&
ufw deny out from any to 192.168.0.0/16 &&
ufw deny out from any to 169.254.0.0/16
ufw enable
# CHECK AFTER RUN FAIRWALL
ping 8.8.8.8