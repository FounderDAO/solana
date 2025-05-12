# solana_monitor_bot.py
import os
import json
import subprocess
import requests
from decimal import Decimal
from ping3 import ping
from datetime import datetime
from pathlib import Path

# === Paths for alert state tracking ===
KYC_EPOCH_FILE = Path(os.path.expanduser("~/solana_python_bot/solana_bot_last_kyc_epoch"))
BALANCE_ALERT_FILE = Path.home() / ".solana_bot_last_balance_alert"

# === Load config.json ===
CONFIG_PATH = os.path.expanduser("~/solana_python_bot/config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

# === Config variables ===
SOLANA_PATH = os.path.expanduser(config["SOLANA_PATH"])
CLUSTER = config["CLUSTER"]
API_URL = config["API_URL"]
BOT_TOKEN = config["BOT_TOKEN"]
CHAT_ID_ALARM = config["CHAT_ID_ALARM"]
CHAT_ID_LOG = config["CHAT_ID_LOG"]
TEXT_INFO_EPOCH = config["TEXT_INFO_EPOCH"]
SKIP_DOP = float(config["skip_dop"])
SEND_INTERVAL_MINUTES = int(config.get("SEND_INTERVAL_MINUTES", 60))

PUB_KEY = config["PUB_KEY"]
VOTE = config["VOTE"]
IP = config["IP"]
BALANCEWARN = config["BALANCEWARN"]
TEXT_NODE = config["TEXT_NODE"]
TEXT_NODE2 = config["TEXT_NODE2"]
TEXT_ALARM = config["TEXT_ALARM"]
INET_ALARM = config["INET_ALARM"]
BALANCE_ALARM = config["BALANCE_ALARM"]
ICON_IP = config["ICON_IP"]
ICON_KYC = config["icon_kycStatus"]
ICON_STATE = config["icon_state"]

now = datetime.now()
send_full_status = now.minute < 1

# === Utility functions ===
def get_balance(pubkey):
    for _ in range(2):
        r = requests.post(API_URL, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [pubkey]
        })
        result = r.json().get("result", {})
        lamports = result.get("value", 0)
        sol = Decimal(lamports) / Decimal(1_000_000_000)
        if sol > 0:
            return round(sol, 2)
    return 0

def send_telegram(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            headers={"Content-Type": "application/json"},
            json={"chat_id": chat_id, "text": text, "parse_mode": "html"}
        )
    except Exception as e:
        print("Telegram Error:", e)

def get_validator_json():
    out = subprocess.check_output([SOLANA_PATH, "validators", f"-u{CLUSTER}", "--output", "json-compact"])
    return json.loads(out)

def get_validator_field(validators, pubkey, field):
    for v in validators.get("validators", []):
        if v.get("identityPubkey") == pubkey:
            return v.get(field)
    return None

def is_new_epoch(current_epoch):
    if not KYC_EPOCH_FILE.exists():
        return True
    try:
        last_epoch = KYC_EPOCH_FILE.read_text().strip()
        return last_epoch != current_epoch
    except:
        return True

def update_kyc_epoch(current_epoch):
    KYC_EPOCH_FILE.write_text(str(current_epoch))

# === Load balance alert state ===
if BALANCE_ALERT_FILE.exists():
    previous_balances = json.loads(BALANCE_ALERT_FILE.read_text())
else:
    previous_balances = {}

# === Epoch Info ===
TEMP_PATH = os.path.expanduser(f"~/solana_python_bot/temp{CLUSTER}.txt")
with open(TEMP_PATH, "w") as f:
    subprocess.run([SOLANA_PATH, "epoch-info", f"-u{CLUSTER}"], stdout=f)

with open(TEMP_PATH) as f:
    lines = f.readlines()

epoch = next((l.split()[1] for l in lines if "Epoch:" in l), "")
epoch_percent = next((l.split()[3] for l in lines if "Epoch Completed Percent" in l), "0")
end_epoch_line = next((l for l in lines if "Epoch Completed Time" in l), "")
end_epoch = end_epoch_line.split("(", 1)[-1].rstrip(")\n").rsplit(" ", 1)[0] if "(" in end_epoch_line else ""

# === Send Epoch Info ===
epoch_msg = (
    f"<b>{TEXT_INFO_EPOCH}</b> <code>\n"
    f"[{epoch}] | [{epoch_percent}%] \n"
    f"End_Epoch {end_epoch}</code>"
)
send_telegram(CHAT_ID_LOG, epoch_msg)

# === Validators JSON ===
validators_json = get_validator_json()
leader_credits = max((v.get("epochCredits", 1) for v in validators_json.get("validators", []) if not v.get("delinquent", False)), default=1)
average = round(validators_json.get("averageStakeWeightedSkipRate", 0), 2)

# === Per-validator loop ===
for i, pubkey in enumerate(PUB_KEY):
    node_name = TEXT_NODE[i]
    vote = VOTE[i]
    ping_ok = ping(IP[i], timeout=3) is not None
    delinquent = get_validator_field(validators_json, pubkey, "delinquent") is True
    balance = get_balance(pubkey)
    balance_str = f"{balance:.2f}"
    key = pubkey
    prev_alerted = previous_balances.get(key, None)

    if balance < BALANCEWARN[i] and prev_alerted != "low":
        alert_text = f"{BALANCE_ALARM[i]}\nBalance:{balance_str}\n{pubkey}"
        print("⚠️ Низкий баланс:", node_name)
        send_telegram(CHAT_ID_ALARM, alert_text)
        previous_balances[key] = "low"
    elif balance >= BALANCEWARN[i]:
        previous_balances[key] = "ok"

    if not ping_ok and delinquent:
        send_telegram(CHAT_ID_ALARM, f"{INET_ALARM[i]} {TEXT_ALARM[i]} {pubkey}")
    elif not ping_ok:
        send_telegram(CHAT_ID_ALARM, f"{INET_ALARM[i]} {pubkey}")
    elif delinquent:
        send_telegram(CHAT_ID_ALARM, f"{TEXT_ALARM[i]} {pubkey}")
    else:
        print("✅ Всё ок:", node_name)
    # === Расчёты для форматированного info_msg ===
    epoch_credits = get_validator_field(validators_json, pubkey, "epochCredits") or 0
    proc = (epoch_credits * 100) / leader_credits if leader_credits else 0

    with open(os.path.expanduser(f"~/solana_python_bot/mesto_top{CLUSTER}.txt")) as f:
        mesto_top = next((line.split()[0] for line in f if pubkey in line), "-")

    # комиссия = ((credits * 5) - (blocks * 3750)) / 1_000_000
    fee = ((epoch_credits * 5) - (produced * 3750)) / 1_000_000
    if fee < 0:
        fee = -fee

    # баланс для отображения
    vote_balance = get_balance(vote)

    info_msg = (
        f"<b>{node_name}</b> [{pubkey[:10]}] <code>\n"
        f"{ICON_IP} {ip}\n"
        f"All:{all_block} Done:{done} skipped:{skipped}\n"
        f"skip:{skip_icon}{skip_rate}% Average:{average:.2f}%\n"
        f"Credits >[{epoch_credits}] [{proc:.2f}%]\n"
        f"Rank    >[{mesto_top}]\n"
        f"Active  >[{active:.2f}]\n"
        f"New     >[{activating:.2f}]{'🟢' if activating > 0 else ''}\n"
        f"Unstake >[{deactivating:.2f}]{'⚠️' if deactivating > 0 else ''}\n"
        f"Balance >[{balance}]  \n"
        f"Vote    >[{vote_balance}]\n"
        f"Fee     >[{fee:.3f} sol]</code>"
    )

    if send_full_status:
        send_telegram(CHAT_ID_LOG, info_msg)
# === Save balance alert state ===
BALANCE_ALERT_FILE.write_text(json.dumps(previous_balances))

# === KYC Info once per epoch ===
if is_new_epoch(epoch):
    for i, pubkey in enumerate(PUB_KEY):
        r = requests.get(f"https://api.solana.org/api/validators/{pubkey}").json()
        state = r.get("state", "N/A")
        kyc = r.get("kycStatus", "N/A")
        info2_msg = (
            f"<b>{TEXT_NODE2[i]} epoch {epoch}</b>[{pubkey[:8]}] <code>\n"
            f"{ICON_STATE} SFDP:{state}\n{ICON_KYC} {kyc}</code>"
        )
        send_telegram(CHAT_ID_LOG, info2_msg)
    update_kyc_epoch(epoch)
