# solana_monitor_bot.py
import os
import json
from pathlib import Path
import subprocess
from time import time
import requests
from decimal import Decimal
from ping3 import ping
from datetime import datetime
from pathlib import Path

now = datetime.now()
send_full_status = True if now.minute < 6 or (now.minute > 28 and now.minute < 30) else False

KYC_EPOCH_FILE = Path(os.path.expanduser("~/solana_python_bot/solana_bot_last_kyc_epoch"))
BALANCE_ALERT_FILE = Path.home() / "~/solana_python_bot/solana_bot_last_balance_alert"

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
TIME_Info2 = int(config["TIME_Info2"])

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


# === Utility functions ===
def get_balance(pubkey):
    for _ in range(2):
        r = requests.post(API_URL, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [pubkey]
        })
        time.sleep(1)
        result = r.json().get("result", {})
        lamports = result.get("value", 0)
        sol = Decimal(lamports) / Decimal(1_000_000_000)
        if sol > 0:
            return round(sol, 2)
    return 0

def send_telegram(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        headers={"Content-Type": "application/json"},
        json={"chat_id": chat_id, "text": text, "parse_mode": "html"}
    )

def get_validator_json():
    out = subprocess.check_output([SOLANA_PATH, "validators", f"-u{CLUSTER}", "--output", "json-compact"])
    return json.loads(out)

def get_validator_field(validators, pubkey, field):
    for v in validators.get("validators", []):
        if v.get("identityPubkey") == pubkey:
            return v.get(field)
    return None

# === Main Execution ===
print("Start date:", datetime.now())
validators_json = get_validator_json()

for i, pubkey in enumerate(PUB_KEY):
    node_name = TEXT_NODE[i]
    ping_ok = ping(IP[i], timeout=3) is not None
    delinquent = get_validator_field(validators_json, pubkey, "delinquent") is True
    balance = get_balance(pubkey)
    balance_str = f"{balance:.2f}"
    key = pubkey
    prev_alerted = previous_balances.get(key, None)

    balance_str = f"{balance:.2f}"
    if balance_str.startswith("."):
        balance_str = "0" + balance_str

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
        print("\u2705 All Good:", node_name)
        
print("End date:", datetime.now())

# === Gossip and validator ranks ===
gossip_path = os.path.expanduser(f"~/solana_python_bot/ip{CLUSTER}.txt")
with open(gossip_path, "w") as f:
    subprocess.run([SOLANA_PATH, "gossip", f"-u{CLUSTER}"], stdout=f)

mesto_top_path = os.path.expanduser(f"~/solana_python_bot/mesto_top{CLUSTER}.txt")
with open(mesto_top_path, "w") as f:
    subprocess.run([SOLANA_PATH, "validators", f"-u{CLUSTER}", "--sort=credits", "-r", "-n"], stdout=f)

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

def send_epoch_info():
    # === Send Epoch Info ===
    epoch_msg = (
        f"<b>{TEXT_INFO_EPOCH}</b> <code>\n"
        f"[{epoch}] | [{epoch_percent}%] \n"
        f"End_Epoch {end_epoch}</code>"
    )
    send_telegram(CHAT_ID_LOG, epoch_msg)
if send_full_status:
    # === Detailed Info per Validator ===
    for i, pubkey in enumerate(PUB_KEY):
        node = TEXT_NODE[i]
        vote = VOTE[i]

        # IP address from gossip
        ip = ""
        with open(gossip_path) as f:
            for line in f:
                if pubkey in line:
                    ip = line.split()[0]
                    break

        # Leader schedule (assigned slots)
        r = requests.post(API_URL, json={
            "jsonrpc": "2.0", "id": 1,
            "method": "getLeaderSchedule",
            "params": [None, {"identity": pubkey}]
        })
        all_block = len(r.json().get("result", {}).get(pubkey, [])) - 2
        all_block = max(all_block, 0)

        # Block production
        r = requests.post(API_URL, json={
            "jsonrpc": "2.0", "id": 1,
            "method": "getBlockProduction",
            "params": [{"identity": pubkey}]
        })
        identity_data = r.json().get("result", {}).get("value", {}).get("byIdentity", {}).get(pubkey, [0, 0])
        done = identity_data[0]
        produced = identity_data[1]
        skipped = done - produced
        skip_rate = round((skipped * 100 / done), 2) if done else 0
        skip_icon = "🟢" if skip_rate <= SKIP_DOP else "🔴"

        # Stakes
        stakes = subprocess.check_output([SOLANA_PATH, "stakes", vote, f"-u{CLUSTER}", "--output", "json-compact"])
        stakes_json = json.loads(stakes)
        active = sum(s.get("activeStake", 0) for s in stakes_json) / 1e9
        activating = sum(s.get("activatingStake", 0) for s in stakes_json) / 1e9
        deactivating = sum(s.get("deactivatingStake", 0) for s in stakes_json) / 1e9

        # epochCredits
        epoch_credits = get_validator_field(validators_json, pubkey, "epochCredits") or 0

        # лидер по кредс — нужен для % расчёта
        leader_pubkey = next((v["identityPubkey"] for v in validators_json["validators"] if not v["delinquent"]), "")
        leader_credits = get_validator_field(validators_json, leader_pubkey, "epochCredits") or 1  # не 0 чтобы избежать деления

        # % от лидера
        proc = (epoch_credits * 100) / leader_credits if leader_credits else 0

        # позиция в топе
        with open(mesto_top_path) as f:
            mesto_top = next((line.split()[0] for line in f if pubkey in line), "-")

        # средний skip rate
        average_temp = validators_json.get("averageStakeWeightedSkipRate", 0)
        average = round(average_temp, 2)

        # комиссия = ((credits * 5) - (blocks * 3750)) / 1_000_000
        fee = ((epoch_credits * 5) - (produced * 3750)) / 1_000_000
        if fee < 0:
            fee = -fee
        
        info_msg = (
            f'<b>{node}</b> [{pubkey[:8]}] <code>\n\n'
            f'{ICON_IP}{ip}\n'
            f'All:{all_block} Done:{done} skipped:{skipped}\n'
            f'skip:{skip_icon}{skip_rate}% Average:{average:.2f}%\n'
            f'Credits >[{epoch_credits}] [{proc:.2f}%]\n'
            f'Rank    >[{mesto_top}]\n'
            f'Active  >[{active:.2f}]\n'
            f'New     >[{activating:.2f}]{"🟢" if activating > 0 else ""}\n'
            f'Unstake >[{deactivating:.2f}]{"⚠️" if deactivating > 0 else ""}\n'
            f'Balance >[{get_balance(pubkey)}]  \n'
            f'Vote    >[{get_balance(vote)}]\n'
            f'Fee     >[{fee:.3f} sol]</code>"'
        )
        if send_full_status:
            send_telegram(CHAT_ID_LOG, info_msg)
            
    if send_full_status:
        send_epoch_info()

# === Info2 Summary (KYС / State) ===
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

