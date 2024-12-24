sudo nano /etc/default/grub

GRUB_CMDLINE_LINUX_DEFAULT="default_hugepagesz=1G hugepagesz=1G hugepages=50"

sudo update-grub
sudo reboot

## Build client
```bash
git clone --recurse-submodules https://github.com/firedancer-io/firedancer.git

cd firedancer

TAG="v0.302.20104"

git checkout $TAG 

git checkout v0.302.20104 

git submodule update

source /opt/rh/gcc-tooltest-12/enable

bash deps.sh

source "$HOME/.cargo/env"

make -j fdctl solana

mkdir -pv -p build/native/gcc/bin/ && cp agave/target/release-with-debug/solana build/native/gcc/bin/solana

export PATH="/root/firedancer/build/native/gcc/bin:$PATH"
```

### Create firedancer user
```bash
sudo adduser firedancer
sudo chown -R firedancer:firedancer /home/firedancer
mkdir -p /home/firedancer/solana
mkdir -p /home/firedancer/solana/ledger
mkdir -p /home/firedancer/solana/snapshots
mkdir -p /home/firedancer/solana/keys
nano /home/firedancer/solana/solana.log
cp /root/solana/.secrets/validator.json /home/firedancer/solana/keys/validator.json && cp /root/solana/.secrets/vote.json /home/firedancer/solana/keys/vote.json
sudo chown -R firedancer:firedancer /home/firedancer/solana/* && sudo chown -R firedancer:firedancer /home/firedancer/solana
sudo chown -R firedancer:firedancer /home/firedancer/mnt && sudo chown -R firedancer:firedancer /home/firedancer/mnt/*
```

### Create solana.toml file
nano /home/firedancer/solana/solana.toml
```bash
name = "FD-Testnet"
user = "firedancer"
dynamic_port_range = "8000-8020"

[log]
    path = "/home/firedancer/solana/solana.log"
    colorize = "auto"
    level_logfile = "INFO"
    level_stderr = "NOTICE"
    level_flush = "WARNING"

[reporting]
    solana_metrics_config = "host=https://metrics.solana.com:8086,db=tds,u=testnet_write,p=c4fa841aa918bf8274e3e2a44d77568d9861b3ea"

[ledger]
    path = "/home/firedancer/solana/ledger"
    accounts_path = "/home/firedancer/solana/ledger"
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
    path = "/home/firedancer/solana/snapshots"
    incremental_path = "/home/firedancer/solana/snapshots/"

[gossip]
    entrypoints = [
      "entrypoint.testnet.solana.com:8001",
      "entrypoint2.testnet.solana.com:8001",
      "entrypoint3.testnet.solana.com:8001",
    ]
    port = 8001

[consensus]
    identity_path = "/home/firedancer/solana/keys/validator.json"
    vote_account_path = "/home/firedancer/solana/keys/vote.json"
    authorized_voter_paths = [
      "/home/firedancer/solana/keys/validator.json"
    ]

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

### Tuning file
### tuning_fd.sh
nano tuning_fd.sh
```bash
#!/bin/bash

# Установка параметров ядра
echo "Устанавливаем параметры ядра..."

echo 1000000 > /proc/sys/vm/max_map_count
echo 1024000 > /proc/sys/fs/file-max
echo 1024000 > /proc/sys/fs/nr_open
echo 2 > /proc/sys/net/ipv4/conf/lo/rp_filter
echo 1 > /proc/sys/net/ipv4/conf/lo/accept_local
echo 1 > /proc/sys/net/core/bpf_jit_enable
echo 0 > /proc/sys/kernel/numa_balancing

# Применяем настройки
sysctl -p || echo "Некоторые параметры могли быть применены временно. Проверь настройки вручную."

echo "Настройки завершены успешно."
```

### CREATE fd.service
# fd.service
nano fd.service
```bash
[Unit]
Description=Fracendancer Validator
After=network.target

[Service]
ExecStart=/bin/bash -c ' \
     ~/firedancer/build/native/gcc/bin/fdctl configure init all --config /home/firedancer/solana/solana.toml && \
     ~/firedancer/build/native/gcc/bin/fdctl run --config /home/firedancer/solana/solana.toml '

[Install]
WantedBy=multi-user.target
```
cp /root/solana/.secrets/validator.json /home/firedancer/solana/keys/validator.json && cp /root/solana/.secrets/vote.json /home/firedancer/solana/keys/vote.json

solana config set --url https://api.testnet.solana.com
solana config set --keypair /home/firedancer/solana/keys/validator.json

ln -s /root/firedancer/fd.service /etc/systemd/system
systemctl enable fd.service
systemctl daemon-reload

### IF SOLANA AGAVE VERSION INSTALLED AND USED TO STOP OLD SERVICE FILE AND REMOVE ALL DIRECTORY
systemctl stop solana.service
systemctl disable solana.service

systemctl start fd.service
systemctl status fd.service
sudo journalctl -f -u fd.service

echo "alias flog='tail -f /home/firedancer/solana/solana.log'" >> $HOME/.bashrc
echo "alias ct='solana catchup --our-localhost --follow --log'" >> $HOME/.bashrc

source $HOME/.bashrc