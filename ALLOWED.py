import os
import re
import sys
import uuid
import time
import socket
import hashlib
import webbrowser
from typing import List, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import requests
import urllib3

# Captive Portal များတွင် ဖြစ်ပေါ်တတ်သော SSL Warning များအား စနစ်တကျ ပိတ်ထားခြင်း
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TerminalColors:
    """စနစ်တစ်ခုလုံး၏ Console Output အရောင်များ သတ်မှတ်ချက်။"""
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[1;31m"
    WHITE = "\033[1;37m"
    CYAN = "\033[1;36m"
    MAGENTA = "\033[1;35m"
    GRAY = "\033[1;90m"
    RESET = "\033[0m"


class WiFiPortalManager:
    """WiFidog အခြေခံ Network Gateway Handshakes များနှင့် စစ်ဆေးမှုများကို စီမံခန့်ခွဲသည့် အဓိက Class။"""
    
    def __init__(self, bot_token: str, chat_ids: List[str], portal_url: str) -> None:
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.portal_url = portal_url
        
        self.telegram_channel = "https://t.me/starlinkfreezone"
        self.user_agent = (
            "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36"
        )
        
        # Persistent Network Connection အသုံးပြုရန် Session တည်ဆောက်ခြင်း
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Connection': 'keep-alive'
        })
        self.session.verify = False

    @staticmethod
    def clear_terminal() -> None:
        """OS ပလက်ဖောင်းပေါ်မူတည်၍ Terminal Screen အား ရှင်းလင်းပေးခြင်း။"""
        os.system('clear' if os.name == 'posix' else 'cls')

    @staticmethod
    def print_stream(text: str, delay: float = 0.005) -> None:
        """စာသားများကို ပိုမိုလှပသော UI အနေဖြင့် တစ်လုံးချင်းစီ ရိုက်နှိပ်ပြသခြင်း။"""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    @staticmethod
    def get_deterministic_user_id() -> str:
        """ဖုန်း သို့မဟုတ် ကွန်ပျူတာ၏ Hardware ပေါ်မူတည်၍ အမြဲတမ်းပုံသေသတ်မှတ်ပေးမည့် စိတ်ချရသော User ID ထုတ်ပေးခြင်း။"""
        id_file_path = os.path.expanduser("~/.portal_user_id.dat")
        
        if os.path.exists(id_file_path):
            try:
                with open(id_file_path, "r", encoding="utf-8") as f:
                    saved_id = f.read().strip()
                    if saved_id.startswith("ID-") and len(saved_id) >= 15:
                        return saved_id
            except IOError:
                pass

        try:
            hardware_node = f"{uuid.getnode()}-{os.getlogin() if hasattr(os, 'getlogin') else 'client'}"
            sha256_sig = hashlib.sha256(hardware_node.encode()).hexdigest().upper()
            generated_id = f"ID-{sha256_sig[:4]}-{sha256_sig[4:8]}-{sha256_sig[8:12]}"
        except Exception:
            fallback_rand = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest().upper()
            generated_id = f"ID-{fallback_rand[:4]}-{fallback_rand[4:8]}-{fallback_rand[8:12]}"

        try:
            with open(id_file_path, "w", encoding="utf-8") as f:
                f.write(generated_id)
        except IOError:
            pass

        return generated_id

    @staticmethod
    def resolve_local_mac() -> str:
        """စက်၏ လက်ရှိ MAC Address အား ရှာဖွေဖော်ထုတ်ခြင်း။"""
        try:
            mac_hex = hex(uuid.getnode())[2:].zfill(12)
            formatted_mac = ":".join(mac_hex[i:i+2] for i in range(0, 12, 2))
            if len(formatted_mac) == 17 and formatted_mac != "00:00:00:00:00:00":
                return formatted_mac
        except Exception:
            pass
        return "88:2f:92:d4:c9:e0"

    @staticmethod
    def resolve_gateway_ip() -> str:
        """လက်ရှိချိတ်ဆက်ထားသော Router သို့မဟုတ် Gateway ရောက်ရှိရာ IP အား တွက်ချက်ခြင်း။"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            
            ip_octets = local_ip.split('.')
            if ip_octets[0] in ["192", "10", "172"]:
                ip_octets[-1] = "1"
                return ".".join(ip_octets)
        except Exception:
            pass
        return "192.168.110.1"

    def check_remote_approval(self, user_id: str) -> bool:
        """Telegram Webhook Update မှတစ်ဆင့် Admin များထံမှ အတည်ပြုချက်ရယူထားခြင်း ရှိမရှိ စစ်ဆေးခြင်း။"""
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        try:
            response = self.session.get(url, timeout=6)
            data = response.json()
            if data.get("ok"):
                for item in data.get("result", []):
                    message = item.get("message", {})
                    text = message.get("text", "").strip()
                    sender_id = str(message.get("from", {}).get("id", ""))
                    
                    if sender_id in self.chat_ids and user_id in text:
                        return True
        except requests.RequestException:
            pass
        return False

    def notify_administrative_channels(self, user_id: str, mac: str, gateway: str, status: str) -> None:
        """အသုံးပြုသူ၏ အခြေအနေနှင့် ချိတ်ဆက်မှုမှတ်တမ်းကို Telegram Admin Panel ထံသို့ ပေးပို့ခြင်း။"""
        status_indicator = "🟢" if status == "Approved" else "🟡"
        payload_text = (
            f"{status_indicator} *Portal Session Activity Update*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Client ID:* `{user_id}`\n"
            f"🌐 *MAC Node:* `{mac}`\n"
            f"🚪 *Gateway IP:* `{gateway}`\n"
            f"📊 *State:* {status}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _ဤ ID အား Bot သို့ Forward ပြုလုပ်ခြင်းဖြင့် ခွင့်ပြုချက် (Approve) ပေးနိုင်ပါသည်။_" 
            if status == "Pending" else "🚀 _အသုံးပြုသူအား စနစ်အတွင်းသို့ အောင်မြင်စွာ ခွင့်ပြုပေးလိုက်ပါပြီ။_"
        )
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        for chat_id in self.chat_ids:
            body = {"chat_id": chat_id, "text": payload_text, "parse_mode": "Markdown"}
            try:
                self.session.post(url, json=body, timeout=5)
            except requests.RequestException:
                pass

    @staticmethod
    def render_progress_bar(duration: float = 1.0, label: str = "Processing") -> None:
        """စနစ်၏ လုပ်ဆောင်ချက်အဆင့်ဆင့်ကို မျက်နှာပြင်တွင် စနစ်တကျ Loading ပုံစံပြသပေးခြင်း။"""
        stages = [
            f"{TerminalColors.RED}■■▢▢▢▢▢▢▢▢ 20%",
            f"{TerminalColors.YELLOW}■■■■■■▢▢▢▢ 60%",
            f"{TerminalColors.GREEN}■■■■■■■■■■ 100%"
        ]
        slice_time = duration / len(stages)
        for stage in stages:
            sys.stdout.write(f"\r {TerminalColors.CYAN}⚙ {TerminalColors.WHITE}{label:<24} {stage}{TerminalColors.RESET}")
            sys.stdout.flush()
            time.sleep(slice_time)
        sys.stdout.write(f"\r {TerminalColors.GREEN}✔ {TerminalColors.WHITE}{label:<24} {TerminalColors.GREEN}[ COMPLETE ]{TerminalColors.RESET}\n")
        sys.stdout.flush()

    def display_system_header(self) -> None:
        """စနစ်၏ ခေါင်းစီး Banner အား သပ်ရပ်စွာ ပုံဖော်ပေးခြင်း။"""
        c, w, g, gray = TerminalColors.CYAN, TerminalColors.WHITE, TerminalColors.GREEN, TerminalColors.GRAY
        print(f"{c}╔" + "═" * 68 + "╗")
        print(f"{c}║                 ✦  ENTERPRISE PORTAL INTERFACE HANDSHAKE  ✦        {c}║")
        print(f"{c}║{gray}  Channel : {w}{self.telegram_channel:<25} {gray}│  Version : {g}v2.5 Professional   {gray}║")
        print(f"{c}╚" + "═" * 68 + f"╝{w}\n")

    def _modify_url_parameter(self, url: str, param_name: str, new_value: str) -> str:
        """URL အတွင်းရှိ Query parameter (ဥပမာ- mac) ကို Web Standard တိုင်း အမှားအယွင်းမရှိ ပြောင်းလဲပေးခြင်း။"""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        query_params[param_name] = [new_value]
        
        modified_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            modified_query,
            parsed_url.fragment
        ))

    def run(self) -> None:
        """အဓိက စနစ်တစ်ခုလုံးကို စတင်လည်ပတ်စေသော Function ဖြစ်သည်။"""
        self.clear_terminal()
        self.display_system_header()
        
        client_id = self.get_deterministic_user_id()
        mac_addr = self.resolve_local_mac()
        gw_ip = self.resolve_gateway_ip()
        
        print(f" {TerminalColors.YELLOW}⚡ ဒေသတွင်း Gateway Network ပတ်ဝန်းကျင်အား စစ်ဆေးနေပါသည်...{TerminalColors.RESET}\n")
        self.render_progress_bar(duration=0.4, label="Resolving Node Attributes")
        self.render_progress_bar(duration=0.4, label="Verifying Remote Session Token")
        
        approved = self.check_remote_approval(client_id)
        
        if not approved:
            self.notify_administrative_channels(client_id, mac_addr, gw_ip, "Pending")
            print(f"\n {TerminalColors.RED}🛑 Verification Pending: အသုံးပြုခွင့် သတ်မှတ်ချက် လိုအပ်နေပါသည်!{TerminalColors.RESET}")
            print(f" {TerminalColors.GRAY}╔" + "═" * 58 + "╗")
            print(f" {TerminalColors.GRAY}║ {TerminalColors.WHITE}သင့်စက်၏ ID : {TerminalColors.GREEN}{client_id:<43} {TerminalColors.GRAY}║")
            print(f" {TerminalColors.GRAY}╚" + "═" * 58 + "╝")
            print(f" {TerminalColors.YELLOW}📢 စနစ်အတွင်း အသုံးပြုခွင့်ရရန် သင့် Device ID ကို ကူးယူပြီး အုပ်ချုပ်သူထံ တင်ပြပါ-")
            print(f" {TerminalColors.CYAN}➜ Operations Directory: {TerminalColors.WHITE}{self.telegram_channel}{TerminalColors.RESET}\n")
            return

        self.notify_administrative_channels(client_id, mac_addr, gw_ip, "Approved")
        
        print(f"\n {TerminalColors.CYAN}┌───────────────────────── System Specification ─────────────────────────┐")
        print(f" {TerminalColors.CYAN}│ {TerminalColors.WHITE}Registered ID  {TerminalColors.GRAY}➜  {TerminalColors.GREEN}{client_id:<48} {TerminalColors.CYAN}│")
        print(f" {TerminalColors.CYAN}│ {TerminalColors.WHITE}Access Status  {TerminalColors.GRAY}➜  {TerminalColors.GREEN}VERIFIED / ACTIVATED ENGINE PRIVILEGE ✅        {TerminalColors.CYAN}│")
        print(f" {TerminalColors.CYAN}│ {TerminalColors.WHITE}Target Hardware{TerminalColors.GRAY}➜  {TerminalColors.YELLOW}{mac_addr:<18} {TerminalColors.WHITE}Gateway IP{TerminalColors.GRAY} ➜ {TerminalColors.YELLOW}{gw_ip:<17} {TerminalColors.CYAN}│")
        print(f" {TerminalColors.CYAN}└──────────────────────────────────────────────────────────────────────┘\n")
        
        self.render_progress_bar(duration=0.3, label="Formulating Frame Payload")
        self.render_progress_bar(duration=0.3, label="Binding Device Interfaces")

        processed_url = self._modify_url_parameter(self.portal_url, 'mac', mac_addr)
        
        print(f"\n {TerminalColors.GREEN}✔ Target definitions cleanly set.")
        print(f" {TerminalColors.CYAN}🌐 Browser Engine အတွင်းသို့ Auth Portal လင့်ခ်အား ချိတ်ဆက်ပေးနေပါသည်...{TerminalColors.RESET}\n")
        time.sleep(0.8)

        try:
            webbrowser.open(processed_url)
            print(f" {TerminalColors.GREEN}┌" + "─" * 68 + "┐")
            self.print_stream(f" {TerminalColors.GREEN}│  ✔ Portal အား Browser သို့ အောင်မြင်စွာ ပို့ဆောင်ပြီးပါပြီ။                 │")
            print(f" {TerminalColors.GREEN}└" + "─" * 68 + "┘")
        except Exception:
            print(f"\n {TerminalColors.RED}✖ Browser အလိုအလျောက် မပွင့်လာပါက အောက်ပါလင့်ခ်ကို ကိုယ်တိုင်ဖွင့်ပါ:\n {TerminalColors.WHITE}{processed_url}{TerminalColors.RESET}")
        print()


if __name__ == "__main__":
    # ပြင်ပမှ ချိန်ညှိရမည့် အချက်အလက်များအား သီးသန့်ခွဲထုတ်ထားခြင်း
    BOT_API_TOKEN = "8950422075:AAGlHOrdaqMwzxxMO3r_A3QwI8e1HzGS3Iw"
    ADMIN_CHAT_IDS = ["8404894106", "7592705124"]
    PORTAL_ENDPOINT_URL = (
        "https://portal-as.ruijienetworks.com/api/auth/wifidog?stage=portal&"
        "gw_id=984a6b9da30e&gw_sn=H1TA1EN003183&gw_address=192.168.110.1&"
        "gw_port=2060&ip=192.168.110.189&mac=88:2f:92:d4:c9:e0&slot_num=14&"
        "nasip=192.168.1.198&ssid=VLAN233&ustate=0&mac_req=1&url=http%3A%2F%2F192.168.0.1%2F&"
        "chap_id=%5C361&chap_challenge=%5C155%5C234%5C000%5C201%5C352%5C275%5C342%5C210%5C202%5C327%5C272%5C071%5C026%5C330%5C115%5C266"
    )

    try:
        engine = WiFiPortalManager(
            bot_token=BOT_API_TOKEN, 
            chat_ids=ADMIN_CHAT_IDS, 
            portal_url=PORTAL_ENDPOINT_URL
        )
        engine.run()
    except KeyboardInterrupt:
        print(f"\n\n {TerminalColors.RED}⚠ အသုံးပြုသူမှ လုပ်ဆောင်ချက်ကို ရပ်ဆိုင်းလိုက်သဖြင့် စနစ်ကို ပိတ်လိုက်ပါသည်။{TerminalColors.RESET}\n")
