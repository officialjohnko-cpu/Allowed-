import os
import re
import socket
import json
import base64
import time
import sys
import itertools
import threading
from typing import Optional, Dict, Any
import requests
import urllib3

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Colors:
    """Terminal color codes (ANSI) with fallback for non-TTY."""
    if sys.stdout.isatty():
        GREEN = "\033[1;32m"
        YELLOW = "\033[1;33m"
        RED = "\033[1;31m"
        WHITE = "\033[1;00m"
        CYAN = "\033[1;36m"
        MAGENTA = "\033[1;35m"
        BLUE = "\033[1;34m"
        BOLD = "\033[1m"
        DIM = "\033[2m"
        RESET = "\033[0m"
    else:
        GREEN = YELLOW = RED = WHITE = CYAN = MAGENTA = BLUE = BOLD = DIM = RESET = ""

    @staticmethod
    def gradient(text: str, colors: list) -> str:
        if not sys.stdout.isatty():
            return text
        result = ""
        for i, char in enumerate(text):
            result += colors[i % len(colors)] + char
        return result + Colors.RESET


class Spinner:
    """A simple terminal spinner to indicate activity."""
    def __init__(self, message="Processing", style="dots"):
        self.message = message
        self.running = False
        self.thread = None
        self.styles = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "line": ["|", "/", "-", "\\"],
            "braille": ["⠋", "⠙", "⠚", "⠞", "⠖", "⠦", "⠴", "⠲", "⠳", "⠓"]
        }
        self.frames = self.styles.get(style, self.styles["dots"])

    def spin(self):
        for frame in itertools.cycle(self.frames):
            if not self.running:
                break
            sys.stdout.write(f"\r{Colors.CYAN}{frame} {self.message}{Colors.RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self.message)+10) + "\r")

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()

    def stop(self, success=True):
        self.running = False
        if self.thread:
            self.thread.join()
        if success:
            sys.stdout.write(f"\r{Colors.GREEN}✓ {self.message}{Colors.RESET}\n")
        else:
            sys.stdout.write(f"\r{Colors.RED}✗ {self.message}{Colors.RESET}\n")


class WiFiBypassTool:
    CONFIG_FILE = "config_johnko.json"
    AUTH_ENDPOINT = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
    USER_AGENT = (
        "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36"
    )

    def __init__(self) -> None:
        self.config: Dict[str, str] = self.load_config()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.USER_AGENT})
        self.session.verify = False
        self.version = "3.0.0"

    @staticmethod
    def clear_screen() -> None:
        os.system('clear' if os.name == 'posix' else 'cls')

    @staticmethod
    def animate_text(text: str, delay: float = 0.03) -> None:
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    def print_banner(self) -> None:
        c = Colors
        print(f"{c.CYAN}╔{'═'*48}╗")
        print(f"{c.CYAN}║{c.BOLD}  🚀 ELONMUSK WiFi Bypass Tool v{self.version}  {c.CYAN}║")
        print(f"{c.CYAN}║{c.BOLD}  👤 Developer: {c.YELLOW}JOHN KO{c.CYAN}                  ║")
        print(f"{c.CYAN}║{c.BOLD}  📢 Telegram: {c.MAGENTA}https://t.me/npvvpnoldversion{c.CYAN}║")
        print(f"{c.CYAN}╚{'═'*48}╝{c.RESET}")

    def load_config(self) -> Dict[str, str]:
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def save_config(self) -> None:
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"{Colors.RED}✘ Failed to save config: {e}{Colors.RESET}")

    def _get_local_gateway(self) -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(1)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            parts = ip.split('.')
            parts[-1] = '1'
            return '.'.join(parts)
        except Exception:
            return "192.168.110.1"

    def auto_catch_portal(self) -> None:
        self.clear_screen()
        c = Colors
        print(f"{c.CYAN}╔{'═'*48}╗")
        print(f"{c.CYAN}║{c.BOLD}  🔍 PORTAL URL DETECTOR           {c.CYAN}║")
        print(f"{c.CYAN}╚{'═'*48}╝{c.RESET}\n")

        print(f"{c.YELLOW}➜ Initializing network scan...{c.RESET}\n")

        gateways = [self._get_local_gateway(), "192.168.110.1", "192.168.0.1", "10.44.77.254"]
        gateways = list(dict.fromkeys(gateways))

        portal_url: Optional[str] = None
        found_gateway = None

        spinner = Spinner("Scanning gateways", "dots")
        spinner.start()

        for gw in gateways:
            target = f"http://{gw}"
            try:
                res = self.session.get(target, timeout=3, allow_redirects=True)
                if "portal-as.ruijienetworks.com" in res.url:
                    portal_url = res.url
                    found_gateway = gw
                    break
                match = re.search(r"href=['\"](.*?)['\"]", res.text)
                if match and "portal-as.ruijienetworks.com" in match.group(1):
                    extracted = match.group(1)
                    portal_url = extracted if extracted.startswith("http") else "https://portal-as.ruijienetworks.com" + extracted
                    found_gateway = gw
                    break
            except requests.exceptions.RequestException:
                continue

        spinner.stop(success=portal_url is not None)

        if not portal_url:
            spinner = Spinner("Trying alternative detection", "line")
            spinner.start()
            try:
                res = self.session.get("http://httpbin.org/get", timeout=5)
                if "portal-as.ruijienetworks.com" in res.url:
                    portal_url = res.url
                else:
                    match = re.search(r"href=['\"](.*?)['\"]", res.text)
                    if match and "portal-as.ruijienetworks.com" in match.group(1):
                        portal_url = match.group(1)
            except requests.exceptions.RequestException:
                pass
            spinner.stop(success=portal_url is not None)

        if portal_url:
            api_url = portal_url.replace("/auth/wifidogAuth/login/?", "/api/auth/wifidog?stage=portal&")
            api_url = api_url.replace("/auth/wifidogAuth/login?", "/api/auth/wifidog?stage=portal&")

            self.config["session_url"] = api_url
            self.save_config()

            b64_url = base64.b64encode(api_url.encode()).decode()

            print(f"\n{c.GREEN}╔{'═'*48}╗")
            print(f"{c.GREEN}║{c.BOLD}  ✓ PORTAL URL CAPTURED!           {c.GREEN}║")
            print(f"{c.GREEN}╚{'═'*48}╝{c.RESET}\n")
            print(f"{c.CYAN}📍 Gateway:{c.WHITE} {found_gateway if found_gateway else 'Auto-detected'}")
            print(f"{c.CYAN}📍 Portal API URL:{c.WHITE}")
            print(f"{c.YELLOW}{'─'*50}")
            print(f"{c.WHITE}{api_url}")
            print(f"{c.YELLOW}{'─'*50}")
            print(f"{c.DIM}📦 Base64: {b64_url}{c.RESET}\n")
        else:
            print(f"\n{c.RED}╔{'═'*48}╗")
            print(f"{c.RED}║{c.BOLD}  ✗ PORTAL NOT FOUND!              {c.RED}║")
            print(f"{c.RED}╚{'═'*48}╝{c.RESET}")
            print(f"\n{c.YELLOW}💡 Make sure you're connected to the Wi-Fi and the captive portal is active.{c.RESET}")

        input(f"\n{c.YELLOW}Press Enter to continue...{c.RESET}")

    def bypass_with_voucher(self) -> None:
        self.clear_screen()
        c = Colors
        print(f"{c.CYAN}╔{'═'*48}╗")
        print(f"{c.CYAN}║{c.BOLD}  🔑 VOUCHER BYPASS                 {c.CYAN}║")
        print(f"{c.CYAN}╚{'═'*48}╝{c.RESET}\n")

        if not self.config.get("session_url"):
            print(f"{c.YELLOW}⚠ No portal URL saved. Detect one now? (y/n){c.RESET}")
            if input(f"{c.CYAN}➜ {c.RESET}").strip().lower() == 'y':
                self.auto_catch_portal()
            if not self.config.get("session_url"):
                print(f"{c.RED}✘ Cannot proceed without portal URL.{c.RESET}")
                input(f"{c.YELLOW}Press Enter...{c.RESET}")
                return

        voucher = self.config.get("voucher", "")
        if voucher:
            print(f"{c.CYAN}Saved voucher: {c.GREEN}{voucher}{c.RESET}")
            use_saved = input(f"{c.YELLOW}Use this voucher? (y/n): {c.RESET}").strip().lower()
            if use_saved != 'y':
                voucher = ""

        if not voucher:
            voucher = input(f"{c.CYAN}➜ Enter voucher code (6-8 digits): {c.RESET}").strip()
            if not re.match(r'^\d{6,8}$', voucher):
                print(f"{c.RED}✘ Invalid voucher format. Must be 6-8 digits.{c.RESET}")
                input(f"{c.YELLOW}Press Enter...{c.RESET}")
                return

        mac = self.config.get("mac_address", "")
        if not mac:
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                            for elements in range(0,2*6,2)][::-1])
            self.config["mac_address"] = mac
            self.save_config()

        print(f"\n{c.CYAN}⏳ Submitting voucher...{c.RESET}")

        spinner = Spinner("Authenticating", "braille")
        spinner.start()

        try:
            payload = {
                "voucher": voucher,
                "mac": mac,
                "stage": "portal"
            }
            resp = self.session.post(
                self.config["session_url"],
                data=payload,
                timeout=10
            )
            spinner.stop(success=True)

            try:
                result = resp.json()
                if result.get("status") == 0 or result.get("success"):
                    print(f"{c.GREEN}╔{'═'*48}╗")
                    print(f"{c.GREEN}║{c.BOLD}  ✓ CONNECTED SUCCESSFULLY!        {c.GREEN}║")
                    print(f"{c.GREEN}╚{'═'*48}╝{c.RESET}")
                    self.config["voucher"] = voucher
                    self.save_config()
                else:
                    msg = result.get("msg", "Unknown error")
                    print(f"{c.RED}╔{'═'*48}╗")
                    print(f"{c.RED}║{c.BOLD}  ✗ AUTH FAILED!                   {c.RED}║")
                    print(f"{c.RED}╚{'═'*48}╝{c.RESET}")
                    print(f"{c.YELLOW}Reason: {msg}{c.RESET}")
            except json.JSONDecodeError:
                if "success" in resp.text.lower():
                    print(f"{c.GREEN}✓ Connection appears successful.{c.RESET}")
                else:
                    print(f"{c.RED}✘ Unexpected server response.{c.RESET}")

        except requests.exceptions.RequestException as e:
            spinner.stop(success=False)
            print(f"{c.RED}✘ Network error: {e}{c.RESET}")

        input(f"\n{c.YELLOW}Press Enter to continue...{c.RESET}")

    def show_code_prices(self) -> None:
        self.clear_screen()
        c = Colors
        print(f"{c.CYAN}╔{'═'*48}╗")
        print(f"{c.CYAN}║{c.GREEN}{c.BOLD}  💰 CODE HACK PRICE LIST        {c.CYAN}║")
        print(f"{c.CYAN}╚{'═'*48}╝{c.RESET}\n")

        print(f"{c.YELLOW}┌─────────────┬────────────┬─────────────┐")
        print(f"{c.YELLOW}│{c.WHITE} Code Length {c.YELLOW}│{c.WHITE} Quantity  {c.YELLOW}│{c.WHITE} Price      {c.YELLOW}│")
        print(f"{c.YELLOW}├─────────────┼────────────┼─────────────┤")
        print(f"{c.YELLOW}│{c.WHITE} 6 Digits    {c.YELLOW}│{c.WHITE} 50 Codes  {c.YELLOW}│{c.WHITE} {c.GREEN}15,000 KS{c.WHITE}  {c.YELLOW}│")
        print(f"{c.YELLOW}├─────────────┼────────────┼─────────────┤")
        print(f"{c.YELLOW}│{c.WHITE} 7 Digits    {c.YELLOW}│{c.WHITE} 50 Codes  {c.YELLOW}│{c.WHITE} {c.GREEN}20,000 KS{c.WHITE}  {c.YELLOW}│")
        print(f"{c.YELLOW}├─────────────┼────────────┼─────────────┤")
        print(f"{c.YELLOW}│{c.WHITE} 8 Digits    {c.YELLOW}│{c.WHITE} 50 Codes  {c.YELLOW}│{c.WHITE} {c.GREEN}25,000 KS{c.WHITE}  {c.YELLOW}│")
        print(f"{c.YELLOW}└─────────────┴────────────┴─────────────┘{c.RESET}\n")

        print(f"{c.MAGENTA}🔑 CODE HACK: NUMBER ONLY{Colors.RESET}")
        print(f"{c.CYAN}📌 Examples: 123456 • 1234567 • 12345678{Colors.RESET}")
        print(f"{c.MAGENTA}✅ 100% Working Codes from Ruijie System{Colors.RESET}")
        print(f"{c.CYAN}📢 Contact: https://t.me/npvvpnoldversion{Colors.RESET}\n")

        print(f"{c.GREEN}💳 Payment Methods:{Colors.RESET}")
        print(f"{c.YELLOW}  📱 Wave Money : 09426313114")
        print(f"{c.YELLOW}  📱 KBZ Pay    : 09262967514 (Su Su Kyi){Colors.RESET}\n")

        input(f"{c.YELLOW}Press Enter to continue...{Colors.RESET}")

    def run(self) -> None:
        while True:
            self.clear_screen()
            self.print_banner()

            c = Colors
            print(f"\n{c.CYAN}┌{'─'*48}┐")
            print(f"{c.CYAN}│{c.BOLD}  MAIN MENU                        {c.CYAN}│")
            print(f"{c.CYAN}├{'─'*48}┤")
            print(f"{c.CYAN}│{c.WHITE}  {c.GREEN}1.{c.WHITE} 🔍 Get Portal URL              {c.CYAN}│")
            print(f"{c.CYAN}│{c.WHITE}  {c.GREEN}2.{c.WHITE} 🔑 Bypass with Voucher         {c.CYAN}│")
            print(f"{c.CYAN}│{c.WHITE}  {c.GREEN}3.{c.WHITE} 💰 Code Hack Price List        {c.CYAN}│")
            print(f"{c.CYAN}│{c.WHITE}  {c.GREEN}4.{c.WHITE} 🚪 Exit Tool                  {c.CYAN}│")
            print(f"{c.CYAN}└{'─'*48}┘{c.RESET}")

            print(f"\n{c.YELLOW}🔑 Code Hack: NUMBER ONLY • 6/7/8 Digits{Colors.RESET}\n")

            choice = input(f"{c.CYAN}➜ Choose [1-4]: {c.RESET}").strip()

            if choice == "1":
                self.auto_catch_portal()
            elif choice == "2":
                self.bypass_with_voucher()
            elif choice == "3":
                self.show_code_prices()
            elif choice == "4":
                print(f"\n{c.MAGENTA}╔{'═'*48}╗")
                print(f"{c.MAGENTA}║{c.BOLD}  👋 GOODBYE! See you again!      {c.MAGENTA}║")
                print(f"{c.MAGENTA}╚{'═'*48}╝{c.RESET}")
                time.sleep(0.8)
                break
            else:
                print(f"\n{c.RED}✘ Invalid choice! Please select 1-4{c.RESET}")
                time.sleep(0.8)


if __name__ == "__main__":
    try:
        tool = WiFiBypassTool()
        tool.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.RED}Exiting...{Colors.RESET}")
        sys.exit(0)