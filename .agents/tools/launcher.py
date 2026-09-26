"""
Greend Malik — Autonomous AI Trading Desk Launcher
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
      {C.BOLD}{C.BRIGHT_WHITE}⚡ GREEND MALIK AI TRADING DESK — BINANCE FUTURES (20x){C.RESET}
      {C.GRAY}🏛️ FRAMEWORK   :{C.RESET} {C.BRIGHT_YELLOW}Institutional Smart Money Concepts & Prop Firm Risk Framework{C.RESET}
      {C.GRAY}🧠 QUANT & ML :{C.RESET} {C.BRIGHT_CYAN}Optuna Hyperopt + Dissimilarity Index Anomaly Gate + Dynamic Pairlist{C.RESET}
      {C.GRAY}🌐 DASHBOARD  :{C.RESET} {C.BRIGHT_CYAN}http://localhost:5000 [GSAP Animated Chalkboard]{C.RESET}
      {C.GRAY}📱 TELEGRAM   :{C.RESET} {C.BRIGHT_GREEN}Notifikasi Instan + Two-Way Remote Controller (/status, /positions){C.RESET}
{C.BRIGHT_CYAN}========================================================================================={C.RESET}
"""
    print(banner)

def ensure_git_sync():
    try:
        import auto_git_sync
        print(f"{C.GRAY}☁️ Memeriksa sinkronisasi data cloud GitHub...{C.RESET}")
        success, msg = auto_git_sync.sync_pull()
        if success:
            print(f"{C.BRIGHT_GREEN}{msg}{C.RESET}")
        else:
            print(f"{C.BRIGHT_YELLOW}{msg}{C.RESET}")
    except Exception:
        pass

def ensure_dashboard():
    ensure_git_sync()
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
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_GREEN}[1] 🤖 FULL DUAL-ENGINE HYBRID AUTOPILOT (1H Swing + 5m Fast Scalper + Delta Sniping){C.RESET} {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_CYAN}[2] 🎯 SWING AUTOPILOT ONLY (1H/4H Big Wave + SMC Trailing + Max R:R){C.RESET}                {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_YELLOW}[3] ⚡ FAST SCALPER ONLY (5m/15m Micro-SMC, ORB Breakout & Anti-Stall){C.RESET}              {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_GREEN}[4] 🟢 LONG-ONLY HYBRID AUTOPILOT (1H Swing + 5m Scalper — Zero Short Drag, PF 2.56){C.RESET}  {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_WHITE}[5] 🧠 HYPEROPT STRATEGY OPTIMIZER (Optuna Bayesian Parameter Search){C.RESET}                {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_CYAN}[6] 🌐 DYNAMIC PAIRLIST PIPELINE (6-Stage Multi-Filter Binance Universe Scanner){C.RESET}    {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_YELLOW}[7] 🔬 ADAPTIVE ML & ANOMALY EVALUATOR (Live Dissimilarity Index / OOD Gate){C.RESET}         {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_GREEN}[8] 🖥️ BUKA WEB DASHBOARD VISUAL DI BROWSER (http://localhost:5000){C.RESET}                   {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.GRAY}[9] ❌ KELUAR{C.RESET}                                                                       {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════╝{C.RESET}")

def get_user_choice(timeout_sec=5):
    default_choice = "2"
    try:
        import telegram_notifier
        cur_mode = telegram_notifier.get_desk_mode().upper()
        if cur_mode == "SWING":
            default_choice = "2"
        elif cur_mode == "SCALP":
            default_choice = "3"
        elif cur_mode == "LONG_ONLY":
            default_choice = "4"
        else:
            default_choice = "1"
    except Exception:
        default_choice = "2"

    mode_label = "[2] 🎯 SWING AUTOPILOT" if default_choice == "2" else f"[{default_choice}] AUTOPILOT"
    print(f"\n{C.GRAY}⏳ Otomatis menjalankan mode {C.BRIGHT_CYAN}{mode_label}{C.GRAY} dalam {timeout_sec} detik jika tidak ada tombol ditekan...{C.RESET}")
    
    valid_choices = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    if sys.platform == "win32":
        import msvcrt
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            remaining = int(timeout_sec - (time.time() - start_time)) + 1
            sys.stdout.write(f"\r  {C.GRAY}👉 Masukkan pilihan Anda [1-9] (Auto-boot dalam {C.BRIGHT_YELLOW}{remaining}s{C.GRAY}): {C.RESET}")
            sys.stdout.flush()
            if msvcrt.kbhit():
                ch = msvcrt.getch().decode("utf-8", errors="ignore").strip()
                if ch in valid_choices:
                    print(f"{ch}\n")
                    return ch
            time.sleep(0.1)
        print(f"{default_choice} (Auto-boot {mode_label})\n")
        return default_choice
    else:
        try:
            val = input(f"👉 Masukkan pilihan Anda [1-9] (default {default_choice}): ").strip()
            return val if val in valid_choices else default_choice
        except Exception:
            return default_choice

def main():
    clear_screen()
    print_banner()
    ensure_dashboard()
    print_menu()
    
    choice = get_user_choice(timeout_sec=5)
    
    watchdog_script = os.path.join(TOOLS_DIR, "watchdog_supervisor.py")
    trading_desk_script = os.path.join(TOOLS_DIR, "trading_desk.py")
    hyperopt_script = os.path.join(TOOLS_DIR, "hyperopt_optimizer.py")
    pairlist_script = os.path.join(TOOLS_DIR, "pairlist_pipeline.py")
    ml_script = os.path.join(TOOLS_DIR, "adaptive_ml_engine.py")
    
    if choice == "1":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_GREEN}🛡️ 🤖 MEMULAI DUAL-ENGINE HYBRID AUTOPILOT + AUTO-HEALING WATCHDOG SUPERVISOR{C.RESET}")
        print(f"{C.GRAY}Fitur: Auto-Healing Supervisor + Dual Engine (1H Swing Macro + 5m Scalper) + Level-2 Delta Sniping{C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", watchdog_script], cwd=ROOT_DIR)
        
    elif choice == "2":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_CYAN}🎯 MEMULAI FULL INSTITUTIONAL SWING AUTOPILOT DESK (1H / 4H MACRO CONFLUENCE){C.RESET}")
        print(f"{C.GRAY}Fitur: 1H/4H SMC + Wyckoff + FVG Retest + Dynamic Trailing (+2R/+3R) + Zero Time-Stop{C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", trading_desk_script, "run", "--mode", "SWING"], cwd=ROOT_DIR)
        
    elif choice == "3":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_YELLOW}⚡ MEMULAI HIGH-FREQUENCY FAST SCALPER DESK (5m/15m MICRO-SMC / ORB BREAKOUT){C.RESET}")
        print(f"{C.GRAY}Target: 1:2.0R s/d 1:3.5R Asymmetric Targets | Anti-Stall 20m Time-Stop | Delta Sniping{C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", trading_desk_script, "run", "--mode", "SCALP"], cwd=ROOT_DIR)

    elif choice == "4":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_GREEN}🟢 🛡️ MEMULAI LONG-ONLY HYBRID AUTOPILOT DESK (ZERO SHORT EXPOSURE){C.RESET}")
        print(f"{C.GRAY}Fitur: Dual Engine (1H Swing + 5m Scalper) | 100% Bullish Edge (PF 2.56) | Bebas Short Trap{C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", trading_desk_script, "run", "--mode", "LONG_ONLY", "--long-only"], cwd=ROOT_DIR)
        
    elif choice == "5":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_WHITE}🧠 MENJALANKAN HYPEROPT STRATEGY PARAMETER OPTIMIZER (OPTUNA BAYESIAN){C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", hyperopt_script, "--symbol", "BTC", "--strategy", "fast_scalper", "--trials", "40", "--target", "sortino"], cwd=ROOT_DIR)
        input(f"\n{C.GRAY}Tekan Enter untuk kembali ke menu...{C.RESET}")
        main()

    elif choice == "6":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_CYAN}🌐 MENJALANKAN CHAINABLE DYNAMIC PAIRLIST PIPELINE (6-STAGE FILTER){C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", pairlist_script, "--run", "--top", "8"], cwd=ROOT_DIR)
        input(f"\n{C.GRAY}Tekan Enter untuk kembali ke menu...{C.RESET}")
        main()

    elif choice == "7":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_YELLOW}🔬 MENJALANKAN ADAPTIVE ML & OUT-OF-DISTRIBUTION ANOMALY EVALUATOR{C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", ml_script, "--symbol", "BTC", "--bar", "1h", "--predict"], cwd=ROOT_DIR)
        input(f"\n{C.GRAY}Tekan Enter untuk kembali ke menu...{C.RESET}")
        main()
        
    elif choice == "8":
        print(f"\n{C.BRIGHT_CYAN}🌐 Membuka browser ke http://localhost:5000 ...{C.RESET}")
        webbrowser.open("http://localhost:5000")
        print(f"{C.BRIGHT_GREEN}Selesai! Web Dashboard terbuka di browser Anda.{C.RESET}\n")
        time.sleep(2)
        
    elif choice == "9":
        print(f"\n{C.GRAY}Menutup AI Trading Desk. Selamat trading!{C.RESET}")
        time.sleep(1)
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.BRIGHT_YELLOW}AI Trading Desk dihentikan oleh pengguna.{C.RESET}")
