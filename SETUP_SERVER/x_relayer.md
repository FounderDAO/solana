mkdir -p /root/x/
scp -P 2283 root@134.119.189.143:/root/x/* /root/x/

mkdir /root/.keys
openssl genrsa --out /root/.keys/private.pem
openssl rsa --in /root/.keys/private.pem --pubout --out /root/.keys/public.pem

solana-keygen new --no-bip39-passphrase --outfile $HOME/.keys/x.json && solana address -k ~/.keys/x.json 

sudo tee /root/.keys/relayer.service > /dev/null <<EOF
[Unit]
Description=Solana transaction relayer
Requires=network-online.target chrony.service
After=network-online.target chrony.service
ConditionPathExists=/root/.keys/x.json
ConditionPathExists=/root/.keys/private.pem
ConditionPathExists=/root/.keys/public.pem

[Service]
Environment="RUST_LOG=info"
Environment="SOLANA_METRICS_CONFIG=host=http://metrics.jito.wtf:8086,db=relayer,u=relayer-operators,p=jito-relayer-write"
Environment=X_BLOCK_ENGINE=http://de.projectx.run:11227
Environment=GRPC_BIND_IP=127.0.0.1
Environment=WEB_SOCKET=127.0.0.1:5050
Environment="PUBLIC_IP=$(wget -q -O - ipinfo.io/ip)"
Environment=GRPC_BIND_IP=127.0.0.1

Type=exec
User=root
Type=simple

ExecStart=/root/x/transaction-relayer \\
--keypair-path /root/.keys/x.json \\
--signing-key-pem-path /root/.keys/private.pem \\
--verifying-key-pem-path /root/.keys/public.pem \\
--webserver-bind-addr $WEB_SOCKET \\
--public-ip $PUBLIC_IP \\
--packet-delay-ms=300 \\
--x-block-engine-url $X_BLOCK_ENGINE

RestartSec=10
Restart=on-failure

StandardOutput=null
StandardError=null
LogRateLimitIntervalSec=0
LogRateLimitBurst=0

[Install]
WantedBy=multi-user.target
EOF

ln -s /root/.keys/x.service /etc/systemd/system && systemctl enable x.service && systemctl status x.service