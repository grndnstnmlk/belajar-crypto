"""
Economic Calendar & Macro News Shield (High-Impact Volatility Guard)
Protects trading capital from brutal slippage, spread widening, and whipsaw stop-outs
caused by Tier-1 Macro US Economic Releases (CPI, PPI, NFP, FOMC, GDP, Fed Rate Decisions).

Key Capabilities:
1. Live Fetch & Cache of ForexFactory / Faireconomy Economic Calendar JSON.
2. Identifies High-Impact USD Macro Events.
3. Automatically triggers 'News Blackout':
   - Freezes opening new positions 30 minutes before and 30 minutes after event release.
   - Triggers pre-emptive Breakeven lock (+0.5R) for active trades inside caution window.
4. Provides structured /news summary for Telegram Bot and Web Dashboard integration.
"""

import json
import os
import ssl
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
CALENDAR_CACHE_FILE = os.path.join(DATA_DIR, "economic_calendar.json")

# WIB is UTC+7
WIB = timezone(timedelta(hours=7))

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CACHE_TTL_SECONDS = 3600  # 1 hour cache

# High impact keywords that violently move crypto and dollar liquidity
HIGH_IMPACT_KEYWORDS = [
    "CPI", "CONSUMER PRICE INDEX", "INFLATION", "FOMC", "FED INTEREST RATE",
    "FEDERAL FUNDS RATE", "POWELL", "NON-FARM", "NFP", "UNEMPLOYMENT RATE",
    "GDP", "CORE PCE", "PCE DEFLATOR", "ISM MANUFACTURING", "JACKSON HOLE"
]

def fetch_economic_calendar(force_refresh=False):
    """
    Fetches economic calendar from remote API or reads from local disk cache.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    now_ts = time.time()

    if not force_refresh and os.path.exists(CALENDAR_CACHE_FILE):
        try:
            mtime = os.path.getmtime(CALENDAR_CACHE_FILE)
            if now_ts - mtime < CACHE_TTL_SECONDS:
                with open(CALENDAR_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

    # Remote fetch
    try:
        req = urllib.request.Request(CALENDAR_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and isinstance(data, list):
                with open(CALENDAR_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                return data
    except Exception as e:
        print(f"[Macro News Shield] Warning: Could not refresh live calendar: {e}", file=sys.stderr)
        if os.path.exists(CALENDAR_CACHE_FILE):
            try:
                with open(CALENDAR_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

    return []

def get_parsed_high_impact_events():
    """
    Extracts and parses all USD high-impact events into UTC and WIB datetimes.
    """
    raw_events = fetch_economic_calendar()
    high_impact = []

    for item in raw_events:
        country = item.get("country", "").upper()
        impact = item.get("impact", "").title()
        title = item.get("title", "").strip()
        title_upper = title.upper()
        date_str = item.get("date", "")

        is_usd = (country == "USD")
        is_high = (impact == "High") or any(k in title_upper for k in HIGH_IMPACT_KEYWORDS)

        if is_usd and is_high and date_str:
            try:
                dt_event = datetime.fromisoformat(date_str)
                dt_utc = dt_event.astimezone(timezone.utc)
                dt_wib = dt_utc.astimezone(WIB)
                high_impact.append({
                    "title": title,
                    "country": country,
                    "impact": impact,
                    "forecast": item.get("forecast", "-"),
                    "previous": item.get("previous", "-"),
                    "dt_utc": dt_utc,
                    "dt_wib": dt_wib,
                    "time_wib_str": dt_wib.strftime("%Y-%m-%d %H:%M WIB"),
                    "time_iso": dt_utc.isoformat()
                })
            except Exception:
                continue

    # Sort chronologically
    high_impact.sort(key=lambda x: x["dt_utc"])
    return high_impact

def audit_news_blackout(buffer_minutes=30):
    """
    Evaluates current time against high-impact macro schedule.
    Returns:
    (is_blackout: bool, blackout_reason: str, next_event: dict or None)
    """
    now_utc = datetime.now(timezone.utc)
    events = get_parsed_high_impact_events()

    if not events:
        return False, "Tidak ada data kalender berita berdampak tinggi.", None

    next_upcoming = None

    for ev in events:
        ev_time = ev["dt_utc"]
        diff_seconds = (ev_time - now_utc).total_seconds()
        diff_minutes = diff_seconds / 60.0

        # Check if currently within blackout window [-buffer, +buffer]
        # (Event occurred within last buffer_minutes OR will occur within next buffer_minutes)
        if -buffer_minutes <= diff_minutes <= buffer_minutes:
            if diff_minutes >= 0:
                time_status = f"akan rilis dalam {int(diff_minutes)} menit"
            else:
                time_status = f"baru saja rilis {abs(int(diff_minutes))} menit yang lalu"

            reason = (
                f"🚨 [NEWS BLACKOUT AKTIF] Berita Makro AS '{ev['title']}' ({ev['country']}) {time_status} "
                f"(Jadwal: {ev['time_wib_str']}). Pembukaan posisi baru dibekukan selama ±{buffer_minutes}m "
                f"demi menghindari slippage & fakeout."
            )
            return True, reason, ev

        # Identify next upcoming event in the future
        if diff_seconds > 0:
            if next_upcoming is None or diff_seconds < (next_upcoming["dt_utc"] - now_utc).total_seconds():
                ev_copy = dict(ev)
                ev_copy["minutes_until"] = round(diff_minutes, 1)
                ev_copy["hours_until"] = round(diff_minutes / 60.0, 1)
                next_upcoming = ev_copy

    if next_upcoming:
        mins = next_upcoming["minutes_until"]
        if mins < 60:
            cd_str = f"{int(mins)} menit"
        else:
            hrs = int(mins // 60)
            rem_m = int(mins % 60)
            cd_str = f"{hrs}j {rem_m}m"
        reason = f"🟢 AMAN (Berita besar berikutnya: '{next_upcoming['title']}' dalam {cd_str} - {next_upcoming['time_wib_str']})"
    else:
        reason = "🟢 AMAN (Tidak ada jadwal berita makro AS berdampak tinggi tersisa untuk pekan ini)."

    return False, reason, next_upcoming

def should_preemptively_protect_positions(caution_window_minutes=45):
    """
    Returns True if an upcoming high impact event is within caution_window_minutes.
    Used by trade_manager to lock breakeven early on open trades.
    """
    now_utc = datetime.now(timezone.utc)
    events = get_parsed_high_impact_events()

    for ev in events:
        diff_minutes = (ev["dt_utc"] - now_utc).total_seconds() / 60.0
        if 0 < diff_minutes <= caution_window_minutes:
            return True, ev, int(diff_minutes)
    return False, None, 0

def format_telegram_news_agenda():
    """
    Generates rich HTML formatted string of this week's High-Impact economic releases.
    """
    events = get_parsed_high_impact_events()
    now_utc = datetime.now(timezone.utc)

    lines = [
        "📰 <b>KALENDER EKONOMI MAKRO AS (HIGH-IMPACT)</b>",
        "<i>Perisai Volatilitas Makro & Berita The Fed / CPI</i>",
        "━━━━━━━━━━━━━━━━━━"
    ]

    is_blackout, blackout_reason, next_ev = audit_news_blackout(30)
    if is_blackout:
        lines.append(f"⚠️ <b>STATUS SHIELD:</b> 🔴 <b>BLACKOUT AKTIF (Order Baru Dibekukan)</b>")
    else:
        lines.append(f"🛡️ <b>STATUS SHIELD:</b> 🟢 <b>AMAN (Normal Autopilot)</b>")

    lines.append("━━━━━━━━━━━━━━━━━━\n<b>Jadwal Berita Pekan Ini:</b>")

    future_events = [e for e in events if (e["dt_utc"] - now_utc).total_seconds() > -3600]

    if not future_events:
        lines.append("<i>Tidak ada jadwal berita USD High-Impact mendatang dalam pekan ini.</i>")
    else:
        for ev in future_events[:6]:
            diff_m = (ev["dt_utc"] - now_utc).total_seconds() / 60.0
            if diff_m < 0:
                badge = "<i>(Baru Rilis)</i>"
            elif diff_m < 120:
                badge = f"🔥 <b>Segera ({int(diff_m)}m lagi)</b>"
            else:
                hrs = int(diff_m // 60)
                rem_m = int(diff_m % 60)
                badge = f"⏳ {hrs}j {rem_m}m lagi"

            lines.append(
                f"• <b>{ev['title']}</b>\n"
                f"  🕒 <code>{ev['time_wib_str']}</code> | {badge}\n"
                f"  📊 Forecast: <code>{ev['forecast']}</code> | Prev: <code>{ev['previous']}</code>"
            )

    lines.append("\n━━━━━━━━━━━━━━━━━━")
    lines.append("<i>💡 Aturan Shield: Order baru dibekukan ±30 menit di sekitar jam berita untuk menghindari fakeout wick.</i>")
    return "\n".join(lines)

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("       📰 MACRO NEWS SHIELD & ECONOMIC CALENDAR AUDIT")
    print("=" * 65)
    is_blk, reason, next_e = audit_news_blackout(30)
    print(f"Status Blackout : {'🔴 DIBEKUKAN' if is_blk else '🟢 AMAN (NORMAL)'}")
    print(f"Audit Diagnostik: {reason}")
    if next_e:
        print(f"\nAcara Terdekat:")
        print(f" * Judul     : {next_e['title']}")
        print(f" * Waktu WIB : {next_e['time_wib_str']}")
        print(f" * Hitung Mundur: {next_e.get('hours_until', 0)} jam ({next_e.get('minutes_until', 0)} menit)")
    print("=" * 65 + "\n")
