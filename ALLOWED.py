import os
import re
import socket
import json
import time
import sys
import hashlib
import uuid
import webbrowser
from typing import Optional
import requests
import urllib3

# Suppress insecure request warnings safely
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Colors:
    """Utility class for terminal text color formatting."""
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[1;31m"
    WHITE = "\033[1;37m"
    CYAN = "\033[1;36m"
    MAGENTA = "\033[1;35m"
    GRAY = "\033[1;90m"
    RESET = "\033[0m"


class WiFiBypassTool:
    # Telegram Bot Settings
    BOT_TOKEN = "8950422075:AAGlHOrdaqMwzxxMO3r_A3QwI8e1HzGS3Iw"
    CHAT_ID = "8404894106"
    TELEGRAM_CHANNEL = "https://t.me/starlinkfreezone"

    FIXED_URL = (
        "https://portal-as.ruijienetworks.com/api/auth/wifidog?stage=portal&"
        "gw_id=984a6b9da30e&gw_sn=H1TA1EN003183&gw_address=192.168.110.1&"
        "gw_port=2060&ip=192.168.110.189&mac=88:2f:92:d4:c9:e0&slot_num=14&"
        "nasip=192.168.1.198&ssid=VLAN233&ustate=0&mac_req=1&url=http%3A%2F%2F192.168.0.1%2F&"
        "chap_id=%5C361&chap_challenge=%5C155%5C234%5C000%5C201%5C352%5C275%5C342%5C210%5C202%5C327%5C272%5C071%5C026%5C330%5C115%5C266"
    )
    
    USER_AGENT = (
        "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36"
    )

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Accept': 'application/json, text/plain, */*',
            'Connection': 'keep-alive'
        })
        self.session.verify = False

    @staticmethod
    def clear_screen() -> None:
        os.system('clear' if os.name == 'posix' else 'cls')

    @staticmethod
    def animate_text(text: str, delay: float = 0.01) -> None:
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    @staticmethod
    def generate_user_id() -> str:
        """ဖုန်းတစ်လုံးချင်းစီအတွက် ထူးခြားပြီး အမြဲတမ်းတူညီနေမယ့် ID ထုတ်ပေးခြင်း"""
        try:
            node = uuid.getnode()
            hash_object = hashlib.sha256(str(node).encode())
            hex_dig = hash_object.hexdigest().upper()
            return f"ELON-{hex_dig[:4]}-{hex_dig[4:8]}-{hex_dig[8:12]}"
        except Exception:
            return "ELON-UNKNOWN-USER"

    @staticmethod
    def detect_mac_address() -> str:
        try:
            mac_num = hex(uuid.getnode())[2:].zfill(12)
            formatted_mac = ":".join(mac_num[i:i+2] for i in range(0, 12, 2))
            if len(formatted_mac) == 17:
                return formatted_mac
        except Exception:
            pass
        return "88:2f:92:d4:c9:e0"

    @staticmethod
    def detect_gateway_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            ip_parts = local_ip.split('.')
            if ip_parts[0] in ["192", "10", "172"]:
                ip_parts[-1] = "1"
                return ".".join(ip_parts)
        except Exception:
            pass
        return "192.168.110.1"

    def check_approval(self, user_id: str) -> bool:
        """Admin ထံမှ ခွင့်ပြုချက် ရ၊ မရ စစ်ဆေးခြင်း (Bot Updates ထဲတွင် ID ရှိ၊ မရှိ စစ်သည်)"""
        url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/getUpdates"
        try:
            response = requests.get(url, timeout=5).json()
            if response.get("ok"):
                for result in response.get("result", []):
                    message = result.get("message", {})
                    text = message.get("text", "").strip()
                    from_id = str(message.get("from", {}).get("id", ""))
                    
                    # Admin ဆီက လာတဲ့စာဖြစ်ပြီး အသုံးပြုသူရဲ့ ID နှင့် တိုက်ရိုက်တူညီပါက ခွင့်ပြုမည်
                    if from_id == self.CHAT_ID and user_id in text:
                        return True
        except Exception:
            pass
        return False

    def alert_admin(self, user_id: str, mac: str, gateway: str, status: str) -> None:
        """အသုံးပြုသူ အချက်အလက်ကို Admin ထံ လှမ်းပို့ခြင်း"""
        emoji = "✅" if status == "Approved" else "❌"
        message = (
            f"{emoji} *User Status Update*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User ID:* `{user_id}`\n"
            f"🌐 *MAC Target:* `{mac}`\n"
            f"🚪 *Gateway Target:* `{gateway}`\n"
            f"📊 *Status:* {status}\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _ဒီ User ကို ခွင့်ပြုလိုပါက ဤ ID ကို Bot ဆီသို့ စာသားပြန်ပို့ပေးပါ။_" if status == "Pending" else ""
        )
        url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": self.CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass

    @staticmethod
    def animate_loading_bar(duration: float = 1.0, description: str = "Processing") -> None:
        frames = [
            f"{Colors.RED}██░░░░░░░░ 20%",
            f"{Colors.YELLOW}██████░░░░ 60%",
            f"{Colors.GREEN}██████████ 100%"
        ]
        
        interval = duration / len(frames)
        for frame in frames:
            sys.stdout.write(f"\r {Colors.CYAN}⚙ {Colors.WHITE}{description:<22} {frame}{Colors.RESET}")
            sys.stdout.flush()
            time.sleep(interval)
        sys.stdout.write(f"\r {Colors.GREEN}✔ {Colors.WHITE}{description:<22} {Colors.GREEN}[ COMPLETE ]{Colors.RESET}\n")
        sys.stdout.flush()

    def print_banner(self) -> None:
        c, r, y, g, m, w, gray = Colors.CYAN, Colors.RED, Colors.YELLOW, Colors.GREEN, Colors.MAGENTA, Colors.WHITE, Colors.GRAY
        
        print(f"{c}╭" + "─" * 76 + f"╮")
        print(f"{c}│{r}   ███████╗██╗      ██████╗ ███╗   ██╗███╗   ███╗██╗   ██╗███████╗██╗  ██╗   {c}│")
        print(f"{c}│{r}   ██╔════╝██║     ██╔═══██╗████╗  ██║████╗ ████║██║   ██║██╔════╝██║ ██╔╝   {c}│")
        print(f"{c}│{y}   █████╗  ██║     ██║   ██║██╔██╗ ██║██╔████╔██║██║   ██║███████╗█████╔╝    {c}│")
        print(f"{c}│{y}   ██╔══╝  ██║     ██║   ██║██║╚██╗██║██║╚██╔╝██║██║   ██║╚════██║██╔═██╗    {c}│")
        print(f"{c}│{g}   ███████╗███████╗╚██████╔╝██║ ╚████║██║ ╚═╝ ██║╚██████╔╝███████║██║  ██╗   {c}│")
        print(f"{c}│{g}   ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝   {c}│")
        print(f"{c}├" + "─" * 76 + f"┤")
        print(f"{c}│{m}                       ✦  ELONMUSK WI-FI BYPASS  ✦                         {c}│")
        print(f"{c}│{gray}  Developer : {w}JOHN KO | @JohnKo{gray}         Community : {w}t.me/starlinkfreezone{gray}     {c}│")
        print(f"{c}╰" + "─" * 76 + f"╯{w}\n")

    def _replace_mac(self, url: str, new_mac: str) -> str:
        return re.sub(r'([?&]mac=)[^&]*', r'\g<1>' + new_mac, url)

    def execute_bypass(self) -> None:
        self.clear_screen()
        self.print_banner()
        
        session_url = self.FIXED_URL
        user_id = self.generate_user_id()
        mac_address = self.detect_mac_address()
        gateway_ip = self.detect_gateway_ip()
        
        print(f" {Colors.YELLOW}⚙ စစ်ဆေးမှုများ လုပ်ဆောင်နေပါသည်...{Colors.RESET}\n")
        self.animate_loading_bar(duration=0.6, description="Checking Authorization")
        
        # ခွင့်ပြုချက် အခြေအနေအား စစ်ဆေးခြင်း
        is_approved = self.check_approval(user_id)
        
        if not is_approved:
            # Admin ထံ စာပို့ခြင်း (Pending အနေဖြင့်)
            self.alert_admin(user_id, mac_address, gateway_ip, "Pending")
            
            print(f"\n {Colors.RED}❌ သင်သည် အသုံးပြုခွင့် မရှိသေးပါ!{Colors.RESET}")
            print(f" ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f" 🔑 သင်၏ User ID: {Colors.GREEN}{user_id}{Colors.RESET}")
            print(f" ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f" {Colors.YELLOW}💡 အသုံးပြုခွင့် (Approval) ရယူရန် အောက်ပါ Telegram Channel သို့ ဆက်သွယ်ပါ-")
            print(f" ➜ {Colors.CYAN}{self.TELEGRAM_CHANNEL}{Colors.RESET}\n")
            return

        # ခွင့်ပြုချက်ရပြီးပါက Admin ထံ အောင်မြင်ကြောင်း စာပို့ခြင်း
        self.alert_admin(user_id, mac_address, gateway_ip, "Approved")
        
        # Environment Section Panel
        print(f"\n {Colors.CYAN}╭─[ System Information ]" + "─" * 52)
        print(f" {Colors.CYAN}│ {Colors.WHITE}Your User ID     {Colors.GRAY}➜  {Colors.GREEN}{user_id:<22}")
        print(f" {Colors.CYAN}│ {Colors.WHITE}Status           {Colors.GRAY}➜  {Colors.GREEN}AUTHORIZED ✅")
        print(f" {Colors.CYAN}│ {Colors.WHITE}Local MAC Target {Colors.GRAY}➜  {Colors.YELLOW}{mac_address:<22} {Colors.CYAN}│ {Colors.WHITE}Gateway Target {Colors.GRAY}➜  {Colors.YELLOW}{gateway_ip}")
        print(f" {Colors.CYAN}╰" + "─" * 74 + "\n")
        
        self.animate_loading_bar(duration=0.4, description="Initializing Pipeline")
        self.animate_loading_bar(duration=0.4, description="Injecting MAC Address")

        final_url = self._replace_mac(session_url, mac_address)
        
        print(f"\n {Colors.GREEN}✔ ပြင်ဆင်မှု အောင်မြင်ပါသည်။")
        print(f" {Colors.CYAN}🌐 စက်၏ Browser တွင် တရားဝင် Voucher Login Page ကို ဖွင့်ပေးနေပါသည်...{Colors.WHITE}\n")
        time.sleep(1)

        try:
            webbrowser.open(final_url)
            print(f" {Colors.GREEN}╭" + "─" * 74 + "╮")
            self.animate_text(f" {Colors.GREEN}│ ✔ Browser သို့ လွှဲပြောင်းပေးပြီးပါပြီ။ Voucher ကို ထိုနေရာတွင် ထည့်သွင်းပါ။  │", delay=0.005)
            print(f" {Colors.GREEN}╰" + "─" * 74 + "╯")
        except Exception as e:
            print(f"\n {Colors.RED}✖ Browser ဖွင့်၍မရပါ: {e}{Colors.WHITE}")
        print()


if __name__ == "__main__":
    try:
        tool = WiFiBypassTool()
        tool.execute_bypass()
    except KeyboardInterrupt:
        print(f"\n\n {Colors.RED}⚠ လုပ်ငန်းစဉ်ကို အသုံးပြုသူမှ ရပ်တန့်လိုက်ပါသည်။ Exiting...{Colors.WHITE}\n")
