"""
Akademi Crypto — Autonomous AI Trading Desk Mission Control Launcher
Interactive Python-driven terminal menu with ANSI colors and non-blocking timeout.
"""

import os
import sys
import time
import subprocess
import webbrowser

# Enable UTF-8 & Windows Console ANSI Virtual Terminal Sequences
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        os.system("") # Enable ANSI VT100 in Windows 10/11
    except Exception:
        pass

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Colors
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    GRAY = "\033[90m"

TOOLS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(os.path.dirname(TOOLS_DIR))

def clear_screen():
    os.system("cls" if sys.platform == "win32" else "clear")

def print_banner():
    banner = f"""{C.BRIGHT_CYAN}=========================================================================================
 █████╗ ██╗  ██╗ █████╗ ██████╗ ███████╗███╗   ███╗██╗     ██████╗██████╗ ██╗   ██╗██████╗ ████████╗ ██████╗ 
██╔══██╗██║ ██╔╝██╔══██╗██╔══██╗██╔════╝████╗ ████║██║    ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗
███████║█████═╝ ███████║██║  ██║█████╗  ██╔████╔██║██║    ██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║   ██║
██╔══██║██╔═██╗ ██╔══██║██║  ██║██╔══╝  ██║╚██╔╝██║██║    ██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║   ██║
██║  ██║██║ ╚██╗██║  ██║██████╔╝███████╗██║ ╚═╝ ██║██║    ╚██████╗██║  ██║   ██║   ██║        ██║   ╚██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝     ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝    ╚═════╝ 
========================================================================================={C.RESET}
      {C.BOLD}{C.BRIGHT_WHITE}⚡ INSTITUTIONAL-GRADE AUTONOMOUS WORKSTATION — BINANCE FUTURES (20x){C.RESET}
      {C.GRAY}🏛️ KURIKULUM  :{C.RESET} {C.BRIGHT_YELLOW}Akademi Crypto (Module 01 - 05) & Prop Firm Risk Framework{C.RESET}
      {C.GRAY}🌐 DASHBOARD  :{C.RESET} {C.BRIGHT_CYAN}http://localhost:5000 [GSAP Animated Chalkboard]{C.RESET}
      {C.GRAY}📱 TELEGRAM   :{C.RESET} {C.BRIGHT_GREEN}Notifikasi Instan + Two-Way Remote Controller (/status, /positions){C.RESET}
{C.BRIGHT_CYAN}========================================================================================={C.RESET}
"""
    print(banner)

def ensure_dashboard():
    print(f"{C.GRAY}🔄 Memeriksa status Web Dashboard Server (Port 5000)...{C.RESET}")
    srv_script = os.path.join(TOOLS_DIR, "dashboard_server.py")
    if os.path.exists(srv_script):
        try:
            flags = (0x00000008 | 0x00000200 | 0x08000000) if sys.platform == "win32" else 0
            subprocess.Popen(
                [sys.executable, "-u", srv_script],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
                close_fds=True,
                cwd=ROOT_DIR
            )
            time.sleep(1.0)
        except Exception:
            pass
    print(f"{C.BRIGHT_GREEN}🟢 Dashboard siap diakses pada http://localhost:5000{C.RESET}\n")

def print_menu():
    print(f"{C.BRIGHT_CYAN}╔═══════════════════════════════════════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}                      {C.BOLD}{C.BRIGHT_WHITE}🎯 PILIH PRESET OPERASI AUTOPILOT{C.RESET}                               {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}╠═══════════════════════════════════════════════════════════════════════════════════════╣{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_GREEN}[1] 🚀 SWING INTRADAY AUTOPILOT (1H / 4H Macro Confluence - Rekomendasi Utama){C.RESET}       {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_YELLOW}[2] ⚡ FAST SCALPER ENGINE (5m / 15m Micro-SMC, ORB Breakout & Delta Sniping){C.RESET}         {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_WHITE}[3] 🔍 TOTAL SYSTEM DIAGNOSTIC & HEALTH AUDIT (55 Automated Test Suite){C.RESET}             {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_CYAN}[4] 🌐 BUKA WEB DASHBOARD VISUAL SAJA DI BROWSER (http://localhost:5000){C.RESET}            {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.GRAY}[5] ❌ KELUAR{C.RESET}                                                                       {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════╝{C.RESET}")

def get_user_choice(timeout_sec=5):
    print(f"\n{C.GRAY}⏳ Otomatis menjalankan mode {C.BRIGHT_GREEN}[1] SWING INTRADAY{C.GRAY} dalam {timeout_sec} detik jika tidak ada tombol ditekan...{C.RESET}")
    
    if sys.platform == "win32":
        import msvcrt
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            remaining = int(timeout_sec - (time.time() - start_time)) + 1
            sys.stdout.write(f"\r  {C.GRAY}👉 Masukkan pilihan Anda [1-5] (Auto-boot dalam {C.BRIGHT_YELLOW}{remaining}s{C.GRAY}): {C.RESET}")
            sys.stdout.flush()
            if msvcrt.kbhit():
                ch = msvcrt.getch().decode("utf-8", errors="ignore").strip()
                if ch in ["1", "2", "3", "4", "5"]:
                    print(f"{ch}\n")
                    return ch
            time.sleep(0.1)
        print("1 (Auto-boot)\n")
        return "1"
    else:
        try:
            val = input(f"👉 Masukkan pilihan Anda [1-5] (default 1): ").strip()
            return val if val in ["1", "2", "3", "4", "5"] else "1"
        except Exception:
            return "1"

def main():
    clear_screen()
    print_banner()
    ensure_dashboard()
    print_menu()
    
    choice = get_user_choice(timeout_sec=5)
    
    trading_desk_script = os.path.join(TOOLS_DIR, "trading_desk.py")
    diag_script = os.path.join(ROOT_DIR, "scratch", "total_system_debug.py")
    
    if choice == "1":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_GREEN}🎯 MEMULAI AUTONOMOUS SWING INTRADAY DESK (1H/4H MACRO CONFLUENCE){C.RESET}")
        print(f"{C.GRAY}Proteksi: SMC Trailing Stop (+2R/+3R), Auto-Breakeven (+1R), Fractional Kelly (2.0%){C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", trading_desk_script, "run", "--mode", "SWING"], cwd=ROOT_DIR)
        
    elif choice == "2":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_YELLOW}⚡ MEMULAI HIGH-FREQUENCY FAST SCALPER DESK (5m/15m SMR / ORB BREAKOUT){C.RESET}")
        print(f"{C.GRAY}Target: 1:2.0R s/d 1:3.5R Asymmetric Targets | Anti-Stall 20m Time-Stop{C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", trading_desk_script, "run", "--mode", "SCALP"], cwd=ROOT_DIR)
        
    elif choice == "3":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_WHITE}🔍 MENJALANKAN TOTAL SYSTEM END-TO-END HEALTH AUDIT (55 TESTS){C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", diag_script], cwd=ROOT_DIR)
        input(f"\n{C.GRAY}Tekan Enter untuk kembali ke menu...{C.RESET}")
        main()
        
    elif choice == "4":
        print(f"\n{C.BRIGHT_CYAN}🌐 Membuka browser ke http://localhost:5000 ...{C.RESET}")
        webbrowser.open("http://localhost:5000")
        print(f"{C.BRIGHT_GREEN}Selesai! Web Dashboard terbuka di browser Anda.{C.RESET}\n")
        time.sleep(2)
        
    elif choice == "5":
        print(f"\n{C.GRAY}Menutup Mission Control. Selamat trading!{C.RESET}")
        time.sleep(1)
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.BRIGHT_YELLOW}Mission Control dihentikan oleh pengguna.{C.RESET}")
