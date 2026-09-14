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
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_GREEN}[1] 🚀 FULL INSTITUTIONAL AUTOPILOT (Adaptive Regime + Dynamic Pairlist + Rolling ML){C.RESET}  {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_YELLOW}[2] ⚡ FAST SCALPER ENGINE (5m / 15m Micro-SMC, ORB Breakout & Delta Sniping){C.RESET}         {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_WHITE}[3] 🧠 HYPEROPT STRATEGY OPTIMIZER (Optuna Bayesian Parameter Search){C.RESET}                {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_CYAN}[4] 🌐 DYNAMIC PAIRLIST PIPELINE (6-Stage Multi-Filter Binance Universe Scanner){C.RESET}    {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_YELLOW}[5] 🔬 ADAPTIVE ML & ANOMALY EVALUATOR (Live Dissimilarity Index / OOD Gate){C.RESET}         {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_WHITE}[6] 🔍 TOTAL SYSTEM DIAGNOSTIC & HEALTH AUDIT (63 Automated Test Suite){C.RESET}             {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.BRIGHT_CYAN}[7] 🖥️ BUKA WEB DASHBOARD VISUAL DI BROWSER (http://localhost:5000){C.RESET}                   {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}║{C.RESET}  {C.GRAY}[8] ❌ KELUAR{C.RESET}                                                                       {C.BRIGHT_CYAN}║{C.RESET}")
    print(f"{C.BRIGHT_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════╝{C.RESET}")

def get_user_choice(timeout_sec=5):
    print(f"\n{C.GRAY}⏳ Otomatis menjalankan mode {C.BRIGHT_GREEN}[1] FULL AUTOPILOT{C.GRAY} dalam {timeout_sec} detik jika tidak ada tombol ditekan...{C.RESET}")
    
    if sys.platform == "win32":
        import msvcrt
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            remaining = int(timeout_sec - (time.time() - start_time)) + 1
            sys.stdout.write(f"\r  {C.GRAY}👉 Masukkan pilihan Anda [1-8] (Auto-boot dalam {C.BRIGHT_YELLOW}{remaining}s{C.GRAY}): {C.RESET}")
            sys.stdout.flush()
            if msvcrt.kbhit():
                ch = msvcrt.getch().decode("utf-8", errors="ignore").strip()
                if ch in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                    print(f"{ch}\n")
                    return ch
            time.sleep(0.1)
        print("1 (Auto-boot)\n")
        return "1"
    else:
        try:
            val = input(f"👉 Masukkan pilihan Anda [1-8] (default 1): ").strip()
            return val if val in ["1", "2", "3", "4", "5", "6", "7", "8"] else "1"
        except Exception:
            return "1"

def main():
    clear_screen()
    print_banner()
    ensure_dashboard()
    print_menu()
    
    choice = get_user_choice(timeout_sec=5)
    
    trading_desk_script = os.path.join(TOOLS_DIR, "trading_desk.py")
    hyperopt_script = os.path.join(TOOLS_DIR, "hyperopt_optimizer.py")
    pairlist_script = os.path.join(TOOLS_DIR, "pairlist_pipeline.py")
    ml_script = os.path.join(TOOLS_DIR, "adaptive_ml_engine.py")
    diag_script = os.path.join(ROOT_DIR, "scratch", "total_system_debug.py")
    
    if choice == "1":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_GREEN}🎯 MEMULAI FULL INSTITUTIONAL AUTOPILOT DESK{C.RESET}")
        print(f"{C.GRAY}Fitur: Dynamic Pairlist + Rolling ML Anomaly Shield + Regime Switcher + SMC Stops (+2R/+3R){C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", trading_desk_script, "run", "--mode", "HYBRID"], cwd=ROOT_DIR)
        
    elif choice == "2":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_YELLOW}⚡ MEMULAI HIGH-FREQUENCY FAST SCALPER DESK (5m/15m MICRO-SMC / ORB BREAKOUT){C.RESET}")
        print(f"{C.GRAY}Target: 1:2.0R s/d 1:3.5R Asymmetric Targets | Anti-Stall 20m Time-Stop | Delta Sniping{C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", trading_desk_script, "run", "--mode", "SCALP"], cwd=ROOT_DIR)
        
    elif choice == "3":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_WHITE}🧠 MENJALANKAN HYPEROPT STRATEGY PARAMETER OPTIMIZER (OPTUNA BAYESIAN){C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", hyperopt_script, "--symbol", "BTC", "--strategy", "fast_scalper", "--trials", "40", "--target", "sortino"], cwd=ROOT_DIR)
        input(f"\n{C.GRAY}Tekan Enter untuk kembali ke menu...{C.RESET}")
        main()

    elif choice == "4":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_CYAN}🌐 MENJALANKAN CHAINABLE DYNAMIC PAIRLIST PIPELINE (6-STAGE FILTER){C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", pairlist_script, "--run", "--top", "8"], cwd=ROOT_DIR)
        input(f"\n{C.GRAY}Tekan Enter untuk kembali ke menu...{C.RESET}")
        main()

    elif choice == "5":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_YELLOW}🔬 MENJALANKAN ADAPTIVE ML & OUT-OF-DISTRIBUTION ANOMALY EVALUATOR{C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", ml_script, "--symbol", "BTC", "--bar", "1h", "--predict"], cwd=ROOT_DIR)
        input(f"\n{C.GRAY}Tekan Enter untuk kembali ke menu...{C.RESET}")
        main()
        
    elif choice == "6":
        clear_screen()
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}")
        print(f"{C.BOLD}{C.BRIGHT_WHITE}🔍 MENJALANKAN TOTAL SYSTEM END-TO-END HEALTH AUDIT (63 TESTS){C.RESET}")
        print(f"{C.BRIGHT_CYAN}========================================================================================={C.RESET}\n")
        subprocess.run([sys.executable, "-u", diag_script], cwd=ROOT_DIR)
        input(f"\n{C.GRAY}Tekan Enter untuk kembali ke menu...{C.RESET}")
        main()
        
    elif choice == "7":
        print(f"\n{C.BRIGHT_CYAN}🌐 Membuka browser ke http://localhost:5000 ...{C.RESET}")
        webbrowser.open("http://localhost:5000")
        print(f"{C.BRIGHT_GREEN}Selesai! Web Dashboard terbuka di browser Anda.{C.RESET}\n")
        time.sleep(2)
        
    elif choice == "8":
        print(f"\n{C.GRAY}Menutup AI Trading Desk. Selamat trading!{C.RESET}")
        time.sleep(1)
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.BRIGHT_YELLOW}AI Trading Desk dihentikan oleh pengguna.{C.RESET}")
