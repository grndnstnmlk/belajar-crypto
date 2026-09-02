"""
Institutional Position Sizing & Risk Calculator
Ensures 1-2% risk compliance, R:R calculation, and USD/IDR conversion.
"""

import argparse
import sys

def calculate_position(balance, risk_pct, entry, sl, tp=None, idr_rate=16500.0):
    if entry <= 0 or sl <= 0 or balance <= 0:
        print("Error: Balance, Entry, and Stop Loss must be positive numbers.")
        sys.exit(1)

    is_long = entry > sl
    direction = "LONG" if is_long else "SHORT"

    sl_distance_abs = abs(entry - sl)
    sl_pct = (sl_distance_abs / entry) * 100

    risk_amount_usd = balance * (risk_pct / 100.0)
    risk_amount_idr = risk_amount_usd * idr_rate

    # Position size = Risk Amount / SL fraction
    position_size_usd = risk_amount_usd / (sl_pct / 100.0)
    position_units = position_size_usd / entry
    position_size_idr = position_size_usd * idr_rate

    # Effective leverage relative to account balance
    effective_leverage = position_size_usd / balance

    rr_ratio = None
    reward_amount_usd = None
    reward_amount_idr = None
    if tp:
        tp_distance_abs = abs(tp - entry)
        rr_ratio = tp_distance_abs / sl_distance_abs
        reward_amount_usd = risk_amount_usd * rr_ratio
        reward_amount_idr = reward_amount_usd * idr_rate

    print("\n=======================================================")
    print(f"       POSITION SIZING & RISK REPORT [{direction}]")
    print("=======================================================")
    print(f"Total Account Balance   : ${balance:,.2f} (Rp {balance * idr_rate:,.0f})")
    print(f"Risk Setting            : {risk_pct:.1f}% per trade")
    print(f"Max Capital At Risk     : ${risk_amount_usd:,.2f} (Rp {risk_amount_idr:,.0f})")
    print("-------------------------------------------------------")
    print(f"Entry Price             : ${entry:,.4f}")
    print(f"Stop Loss Price         : ${sl:,.4f} ({sl_pct:.2f}% distance)")
    if tp:
        print(f"Take Profit Price       : ${tp:,.4f}")
        print(f"Risk-to-Reward (R:R)    : 1 : {rr_ratio:.2f}")
        rr_status = "EXCELLENT (>= 1:2.5)" if rr_ratio >= 2.5 else "ACCEPTABLE (>= 1:2.0)" if rr_ratio >= 2.0 else "SUBOPTIMAL (< 1:2.0 - NOT RECOMMENDED)"
        print(f"R:R Quality             : {rr_status}")
    print("-------------------------------------------------------")
    print(f"Recommended Position    : ${position_size_usd:,.2f} (Rp {position_size_idr:,.0f})")
    print(f"Quantity in Units       : {position_units:,.4f} coins/tokens")
    print(f"Effective Leverage      : {effective_leverage:.2f}x of account equity")

    if effective_leverage <= 1.0:
        print("Execution Mode          : SPOT FRIENDLY (Zero liquidation risk)")
    else:
        print(f"Execution Mode          : FUTURES REQUIRED (~{effective_leverage:.1f}x leverage required)")

    if tp:
        print("-------------------------------------------------------")
        print(f"Estimated Max Loss (SL) : -${risk_amount_usd:,.2f} (-Rp {risk_amount_idr:,.0f})")
        print(f"Estimated Max Win (TP)  : +${reward_amount_usd:,.2f} (+Rp {reward_amount_idr:,.0f})")
    print("=======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Crypto Position Sizing & Risk Calculator")
    parser.add_argument("--balance", type=float, required=True, help="Total account balance in USD")
    parser.add_argument("--risk", type=float, default=1.5, help="Risk percentage per trade (e.g. 1.0, 1.5)")
    parser.add_argument("--entry", type=float, required=True, help="Entry price")
    parser.add_argument("--sl", type=float, required=True, help="Stop loss price")
    parser.add_argument("--tp", type=float, default=None, help="Target Take Profit price")
    parser.add_argument("--rate", type=float, default=16500.0, help="USD to IDR conversion rate")
    args = parser.parse_args()

    calculate_position(args.balance, args.risk, args.entry, args.sl, args.tp, args.rate)

if __name__ == "__main__":
    main()
