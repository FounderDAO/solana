sudo apt update && sudo apt upgrade

curl https://sh.rustup.rs -sSf | sh
source $HOME/.cargo/env

. "$HOME/.cargo/env"


sudo apt install libssl-dev libudev-dev pkg-config zlib1g-dev llvm clang cmake make libprotobuf-dev protobuf-compiler -y

sudo nano /etc/default/grub

GRUB_CMDLINE_LINUX_DEFAULT="default_hugepagesz=1G hugepagesz=1G hugepages=50"

sudo update-grub
sudo reboot

## Build client
```bash
git clone --recurse-submodules https://github.com/firedancer-io/firedancer.git

cd firedancer

TAG="v0.305.20111"

git checkout $TAG 

git checkout v0.305.20111
cd firedancer
git stash
git pull 
git checkout v0.403.20113

git submodule update

make -j fdctl solana

source /opt/rh/gcc-tooltest-12/enable

bash deps.sh

source "$HOME/.cargo/env"

sed -i "/^[ \t]*results\[ 0 \] = pwd\.pw_uid/c results[ 0 ] = 1001;" ~/firedancer/src/app/fdctl/config.c
sed -i "/^[ \t]*results\[ 1 \] = pwd\.pw_gid/c results[ 1 ] = 1002;" ~/firedancer/src/app/fdctl/config.c

make -j fdctl solana

## NOT REQUIRED
mkdir -pv -p build/native/gcc/bin/ && cp agave/target/release-with-debug/solana build/native/gcc/bin/solana

export PATH="/root/firedancer/build/native/gcc/bin:$PATH"



```

### Create firedancer user
```bash
sudo adduser sol
pass 123
login sol

mkdir -p solana
mkdir -p solana/ledger
mkdir -p solana/snapshots
mkdir -p solana/keys
touch solana/solana.log
cd solana/keys
nano validator.json
nano vote.json
solana address -k /home/solana/solana/keys/validator.json && solana address -k /home/solana/solana/keys/vote.json
```

### Create solana.toml file
nano /root/solana.toml
```bash
name = "My-TDS"
user = "solana"
dynamic_port_range = "8000-8020"

[log]
    path = "/home/sol/solana/solana.log"
    colorize = "auto"
    level_logfile = "INFO"
    level_stderr = "NOTICE"
    level_flush = "WARNING"

[reporting]
    solana_metrics_config = "host=https://metrics.solana.com:8086,db=tds,u=testnet_write,p=c4fa841aa918bf8274e3e2a44d77568d9861b3ea"

[ledger]
    path = "/home/sol/solana/ledger"
    accounts_path = "/home/sol/solana/ledger"
    limit_size = 200_000_000
    snapshot_archive_format = "zstd"
    require_tower = false

[rpc]
    port = 8899
    full_api = true
    only_known = true
    transaction_history = false
    extended_tx_metadata_storage = false
    private = true

[snapshots]
    incremental_snapshots = true
    full_snapshot_interval_slots = 25000
    incremental_snapshot_interval_slots = 1000
    maximum_full_snapshots_to_retain = 1
    maximum_incremental_snapshots_to_retain = 2
    path = "/home/sol/solana/snapshots"
    incremental_path = "/home/sol/solana/snapshots"

[gossip]
    entrypoints = [
      "entrypoint.testnet.solana.com:8001",
      "entrypoint2.testnet.solana.com:8001",
      "entrypoint3.testnet.solana.com:8001",
    ]
    port = 8001

[consensus]
    identity_path = "/home/sol/solana/keys/validator.json"
    vote_account_path = "/home/sol/solana/keys/vote.json"

    expected_genesis_hash = "4uhcVJyU9pJkvQyS88uRDiswHXSCkY3zQawwpjk2NsNY"

    known_validators = [
      "5D1fNXzvv5NjV1ysLjirC4WY92RNsVH18vjmcszZd8on",
      "dDzy5SR3AXdYWVqbDEkVFdvSPCtS9ihF5kJkHCtXoFs",
      "Ft5fbkqNa76vnsjYNwjDZUXoTWpP7VYm3mtsaQckQADN",
      "eoKpUABi59aT4rR9HGS3LcMecfut9x7zJyodWWP43YQ",
      "9QxCLckBiJc783jnMvXZubK4wH86Eqqvashtrwvcsgkv"
    ]

[layout]
   affinity = "auto"
   agave_affinity = "auto"
   verify_tile_count = 2
   bank_tile_count = 1
   shred_tile_count = 2

[tiles]
    [tiles.quic]
        max_concurrent_connections = 1024
        max_concurrent_handshakes = 1024
    [tiles.shred]
        max_pending_shred_sets = 512
        shred_listen_port = 8030
```

### CREATE fd.service
nano /root/fd.service
```bash
[Unit]
Description=Fracendancer Validator
After=network.target

[Service]
User=root

[Service]
ExecStart=/bin/bash -c ' \
     ~/firedancer/build/native/gcc/bin/fdctl configure init all --config /root/solana.toml && \
     ~/firedancer/build/native/gcc/bin/fdctl run --config /root/solana.toml '

[Install]
WantedBy=multi-user.target
```

ln -s /root/fd.service /etc/systemd/system
systemctl enable fd.service
systemctl daemon-reload
## OR
systemctl enable solana.service
systemctl daemon-reload


solana config set --url https://api.testnet.solana.com && solana config set --keypair /home/sol/solana/keys/validator.json
solana config set --url https://api.testnet.solana.com && solana config set --keypair /home/ubuntu/solana/keys/validator.json
solana config set --url https://api.testnet.solana.com && solana config set --keypair /home/solana/solana/keys/validator.json


### IF SOLANA AGAVE VERSION INSTALLED AND USED TO STOP OLD SERVICE FILE AND REMOVE ALL DIRECTORY
systemctl stop solana.service
systemctl disable solana.service
### or
systemctl stop fd.service
systemctl disable fd.service 

systemctl start fd.service
systemctl status fd.service
sudo journalctl -f -u fd.service
journalctl -u fd.service --no-pager --lines=50

echo "alias slog='tail -f /mnt/disk1/solana.log'" >> $HOME/.bashrc
echo "alias mod='tail -f /mnt/disk1/solana.log | grep -A 5 'Checking for change to mostly_confirmed_threshold''" >> $HOME/.bashrc

echo "alias slog='tail -f /home/ubuntu/solana/solana.log'" >> $HOME/.bashrc
echo "alias ct='solana catchup --our-localhost --follow --log'" >> $HOME/.bashrc
source $HOME/.bashrc

echo "alias slog='tail -f /mnt/disk1/solana.log'" >> $HOME/.bashrc
echo "alias slog='tail -f /home/sol/solana/solana.log'" >> $HOME/.bashrc
echo "alias slog='tail -f /home/solana/solana/solana.log'" >> $HOME/.bashrc
echo "alias ct='solana catchup --our-localhost --follow --log'" >> $HOME/.bashrc
source $HOME/.bashrc

# UPDATE VERSION

git stash
cd firedancer && git pull
git checkout v0.502.20212 && git branch 
git submodule update
make -j fdctl solana
systemctl restart fd.service
export PATH="/root/firedancer/build/native/gcc/bin:$PATH"

sudo /root/firedancer/build/native/gcc/bin/fdctl configure init all --config /root/solana.toml
sudo /root/firedancer/build/native/gcc/bin/fdctl run --config  /root/solana.toml

solana config set --keypair /home/sol/solana/keys/validator.json

sudo /root/firedancer/build/native/gcc/bin/fdctl configure init all --config /root/solana.toml
sudo /root/firedancer/build/native/gcc/bin/fdctl configure fini all --config /root/solana.toml
sudo /root/firedancer/build/native/gcc/bin/fdctl configure init all --config /root/solana.toml
sudo /root/firedancer/build/native/gcc/bin/fdctl run --config /root/solana.toml

cp /root/solana/.secrets/validator.json /home/firedancer/solana/keys/validator.json && cp /root/solana/.secrets/vote.json /home/firedancer/solana/keys/vote.json


make -j EXTRAS="static" fdctl

do-release-upgrade

sudo chown -R firedancer:firedancer /home/firedancer/solana
sudo chmod -R firedancer:firedancer /home/firedancer/solana


sudo chmod -R sol:sol /root/solana.log
sudo chown -R sol:sol /root/solana.log

sudo chown -R $(whoami) path_to_vue_templates_folder
sudo chown -R sol /home/sol/solana/solana.log
sudo chown -R ubuntu /home/sol/solana/solana.log



```bash
name = "ULA-Testnet"
user = "solana"
dynamic_port_range = "8000-8020"

[log]
    path  = "/dev/null"
    colorize = "auto"
    level_logfile = "INFO"
    level_stderr = "NOTICE"
    level_flush = "WARNING"

[reporting]
    solana_metrics_config = "host=https://metrics.solana.com:8086,db=tds,u=testnet_write,p=c4fa841aa918bf8274e3e2a44d77568d9861b3ea"

[ledger]
    path = "/home/solana/solana/ledger"
    accounts_path = "/home/solana/solana/ledger"
    limit_size = 200_000_000
    snapshot_archive_format = "zstd"
    require_tower = false

[rpc]
    port = 8899
    full_api = true
    only_known = true
    transaction_history = false
    extended_tx_metadata_storage = false
    private = true

[snapshots]
    incremental_snapshots = true
    full_snapshot_interval_slots = 25000
    incremental_snapshot_interval_slots = 1000
    maximum_full_snapshots_to_retain = 1
    maximum_incremental_snapshots_to_retain = 2
    path = "/home/solana/solana/snapshots"
    incremental_path = "/home/solana/solana/snapshots"

[gossip]
    entrypoints = [
      "entrypoint.testnet.solana.com:8001",
      "entrypoint2.testnet.solana.com:8001",
      "entrypoint3.testnet.solana.com:8001",
    ]
    port = 8001

[consensus]
    identity_path = "/opt/solana/keys/validator.json"
    vote_account_path = "CNX9bv9vWpdF5Hj3bHHcQAWQbmc4JfQ53wz63NAfGf3A"

    expected_genesis_hash = "4uhcVJyU9pJkvQyS88uRDiswHXSCkY3zQawwpjk2NsNY"

    known_validators = [
      "5D1fNXzvv5NjV1ysLjirC4WY92RNsVH18vjmcszZd8on",
      "dDzy5SR3AXdYWVqbDEkVFdvSPCtS9ihF5kJkHCtXoFs",
      "Ft5fbkqNa76vnsjYNwjDZUXoTWpP7VYm3mtsaQckQADN",
      "eoKpUABi59aT4rR9HGS3LcMecfut9x7zJyodWWP43YQ",
      "9QxCLckBiJc783jnMvXZubK4wH86Eqqvashtrwvcsgkv"
    ]

[layout]
   affinity = "auto"
   agave_affinity = "auto"
   verify_tile_count = 2
   bank_tile_count = 1
   shred_tile_count = 2

[tiles]
    [tiles.quic]
        max_concurrent_connections = 1024
        max_concurrent_handshakes = 1024
    [tiles.shred]
        max_pending_shred_sets = 512
        shred_listen_port = 8030

    [tiles.bundle]
        enabled = true
        url = "https://testnet.block-engine.jito.wtf"
        tip_distribution_program_addr = "F2Zu7QZiTYUhPd7u9ukRVwxh7B71oA3NMJcHuCHc29P2"
        tip_payment_program_addr = "GJHtFqM9agxPmkeKjHny6qiRKrXZALvvFGiKf11QE7hy"
        tip_distribution_authority = "GZctHpWXmsZC1YHACTGGcHhYxjdRqQvTpYkb9LMvxDib"
        commission_bps = 10000

    [tiles.gui]
        enabled = true
        gui_listen_address = "0.0.0.0"
        gui_listen_port = 80
```

solana-keygen new --no-passphrase -o $HOME/.keys/x.json 
openssl genrsa -out $HOME/.keys/auth 1024 &&
openssl rsa -in $HOME/.keys/auth -pubout -out $HOME/.keys/auth.pub


sudo tee $HOME/.keys/x.service > /dev/null <<EOF
[Unit]
Description=X Transaction Relayer
Requires=network-online.target
After=network-online.target

[Service]
Environment="RUST_LOG=info"
Environment=X_BLOCK_ENGINE=http://de.projectx.run:11227
Environment=GRPC_BIND_IP=127.0.0.1
Environment=WEB_SOCKET=127.0.0.1:5050
Environment="PUBLIC_IP=$(wget -q -O - ipinfo.io/ip)"

User=root
Type=simple

ExecStart=$HOME/x/transaction-relayer \\
--keypair-path $HOME/.keys/relayer.json \\
--signing-key-pem-path $HOME/.keys/auth \\
--verifying-key-pem-path $HOME/.keys/auth.pub \\
--webserver-bind-addr \$WEB_SOCKET \\
--public-ip \$PUBLIC_IP \\
--packet-delay-ms=300 \\
--x-block-engine-url \$X_BLOCK_ENGINE

RestartSec=10
Restart=on-failure
StandardOutput=null
StandardError=null
LogRateLimitIntervalSec=0
LogRateLimitBurst=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl stop relayer.service &&  sudo systemctl disable relayer.service && systemctl stop deezBot.service

sudo systemctl daemon-reload
sudo systemctl stop jito.service &&  sudo systemctl disable jito.service



ln -s /root/.keys/x.service /etc/systemd/system
sudo systemctl enable x.service && sudo systemctl restart x.service

journalctl -n 100 -f -u x.service

journalctl -u x.service --since "12 hours ago" > relayer_logs.txt

147.28.173.31