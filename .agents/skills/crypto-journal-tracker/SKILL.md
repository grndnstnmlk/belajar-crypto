---
name: crypto-journal-tracker
description: Disciplined crypto trade logging, position sizing calculation, and performance tracking skill. Calculates position size, risk-to-reward ratios, drawdown metrics, and maintains trade journal entries synthesized from Akademi Crypto Module 03 (Money Psychology & Trading Plan).
---

# Crypto Journal & Position Sizing Tracker
*Synthesized from Akademi Crypto Module 03 (Money Psychology, 100 Juta Pertama Strategy, & Risk Management)*

This skill enforces strict mathematical risk management and psychological discipline before and after every trade.

---

## 📐 Non-Negotiable Mathematical Rules

1. **The 1% - 2% Risk Rule**: Never risk more than 1% to 2% of total trading account equity on a single setup.
2. **Fixed Invalidation Stop Loss**: The Stop Loss price is determined by the chart structure (Swing Low / High or unmitigated Order Block), NEVER by how much dollar loss you "feel" like taking.
3. **Position Size Scaling**: If your Stop Loss is wide, your position size MUST be smaller. If your Stop Loss is tight, your position size can be larger, keeping the dollar risk constant.
4. **Minimum 1:2 R:R Ratio**: Every setup must offer at least double the profit target compared to the risk taken.

---

## 🛠️ Built-in Position Sizing Calculator

The skill includes a CLI position and risk calculator located at:
[calc_position.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/skills/crypto-journal-tracker/scripts/calc_position.py)

### Usage:
```bash
# Calculate position for $5,000 account, risking 1.5%, entering at $100 with $95 Stop Loss
python .agents/skills/crypto-journal-tracker/scripts/calc_position.py --balance 5000 --risk 1.5 --entry 100 --sl 95 --tp 115
```

---

## 📝 Trade Journal Template

Whenever logging or reviewing a completed trade:

```markdown
### 📖 Trade Log: [COIN] — [LONG/SHORT]
- **Date/Time**: [YYYY-MM-DD HH:MM]
- **Entry Price**: [$X.XX]
- **Exit Price**: [$X.XX]
- **Stop Loss Price**: [$X.XX]
- **Position Size**: [$X,XXX]
- **Net P&L ($)**: [+$XXX.XX / -$XXX.XX]
- **R-Multiple Achieved**: [+2.4R / -1.0R]

#### 🧠 Psychological & Technical Review:
- **Setup Trigger**: [e.g. 4H Bullish OB + 15m CHoCH + FVG Retest]
- **Emotional State**: [Calm / Anxious / FOMO / Disciplined]
- **Mistakes Made**: [Did I move SL? Did I take profit too early? None]
- **Key Lesson**: [Takeaway for next time]
```
