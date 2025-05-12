sudo apt install chrony -y 

nano /etc/chrony/chrony.conf

printf '
server ntp.frankfurt.jito.wtf iburst
server ntp.lab.int iburst
driftfile /var/lib/chrony/drift
makestep 1.0 3
maxupdateskew 100.0
dumpdir /var/lib/chrony
rtcsync
keyfile /etc/chrony.keys
leapsectz right/UTC
logdir /var/log/chrony
' > /etc/chrony.conf

sudo systemctl restart chrony.service && sudo systemctl status chrony.service

server ntp.frankfurt.jito.wtf iburst
server ntp.amsterdam.jito.wtf iburst
server ntp.slc.jito.wtf iburst