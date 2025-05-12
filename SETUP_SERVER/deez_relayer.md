mkdir -p /root/deez/
scp -P 2283 root@x.x.x.x:/root/deez/* /root/deez/

mkdir /root/.keys
openssl genrsa --out /root/.keys/private.pem
openssl rsa --in /root/.keys/private.pem --pubout --out /root/.keys/public.pem

solana-keygen new --no-bip39-passphrase --outfile $HOME/.keys/relayer.json && solana address -k ~/.keys/relayer.json 

## Create relayer.service file 
sudo tee /root/.keys/relayer.service > /dev/null <<EOF
[Unit]
Description=Solana transaction relayer
Requires=network-online.target chrony.service
After=network-online.target chrony.service
ConditionPathExists=/root/.keys/relayer.json
ConditionPathExists=/root/.keys/private.pem
ConditionPathExists=/root/.keys/public.pem

[Service]
Environment="RUST_LOG=info"
Environment="SOLANA_METRICS_CONFIG=host=http://metrics.jito.wtf:8086,db=relayer,u=relayer-operators,p=jito-relayer-write"
Environment=BLOCK_ENGINE_URL=https://frankfurt.mainnet.block-engine.jito.wtf
Environment="PUBLIC_IP=$(wget -q -O - ipinfo.io/ip)"
Environment=GRPC_BIND_IP=127.0.0.1

Type=exec
User=root
Restart=on-failure

# Please check if PATH is correct
ExecStart=/root/deez/jito-transaction-relayer \\
--keypair-path=/root/.keys/relayer.json \\
--signing-key-pem-path=/root/.keys/private.pem \\
--verifying-key-pem-path=/root/.keys/public.pem \\
--block-engine-url \$BLOCK_ENGINE_URL \\
--public-ip \$PUBLIC_IP \\
--packet-delay-ms=300 \\
--grpc-bind-ip \$GRPC_BIND_IP

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload &&
ln -s /root/.keys/relayer.service /etc/systemd/system &&
systemctl daemon-reload && systemctl enable relayer.service

systemctl status relayer.service 
systemctl start relayer.service 