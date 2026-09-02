---
name: crypto-onchain-auditor
description: Specialized on-chain security and DEX token auditing skill. Evaluates token liquidity depth, contract vulnerabilities (honeypots, mint authority, freeze authority), holder concentration, DexScreener metrics, and smart contract risks.
---

# Crypto On-Chain & DEX Auditor Playbook
*Synthesized from Akademi Crypto Module 03 (DEX Trading) & Module 04 (Blockchain Technology & Security)*

Use this skill whenever analyzing a decentralized exchange (DEX) token, meme coin, or new blockchain project before swapping or investing.

---

## 🛑 Non-Negotiable Red Flags (Automatic Fail)

If a token exhibits ANY of the following, **DO NOT BUY**:
1. **Honeypot Function**: Smart contract allows purchases but blocks sells (`transfer()` reverts unless sender is owner).
2. **Buy/Sell Tax > 5%**: Excessive taxes designed to trap and drain retail capital.
3. **Active Mint Authority**: Creator wallet can unilaterally print trillions of new tokens and dump on the liquidity pool.
4. **Unlocked Liquidity**: Liquidity pool (LP tokens) is not locked via stream/vesting or burned to a dead address (`0x00...dead`).
5. **Top 10 Holders own > 30%** (excluding DEX liquidity pools and burned tokens).

---

## 🛠️ Built-in DEX Audit Script

Run the automated DEX security and liquidity auditor:
[audit_dex.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/skills/crypto-onchain-auditor/scripts/audit_dex.py)

### Usage:
```bash
# Audit by token symbol or pair query (e.g. PEPE, JUP, RAY)
python .agents/skills/crypto-onchain-auditor/scripts/audit_dex.py --query JUP

# Audit by specific token contract address
python .agents/skills/crypto-onchain-auditor/scripts/audit_dex.py --address <CONTRACT_ADDRESS>
```

---

## 🔍 Step-by-Step DEX Audit Protocol

### Step 1: Liquidity & Market Depth
- **Liquidity Pool (USD)**:
  - $< \$20,000$: Extreme risk; high slippage, vulnerable to single-whale dumps.
  - $\$50,000 - \$200,000$: Acceptable for micro-cap meme trading with strict sizing.
  - $> \$1,000,000$: Institutional/healthy depth for medium swing trades.
- **Volume to Liquidity Ratio ($\text{Vol}/\text{Liq}$)**:
  - If 24h Volume is 50x higher than total liquidity, be cautious of wash trading bots.

### Step 2: External Verification Tools (Manual Links)
When auditing tokens, verify across trusted scanner platforms:
- **EVM (Ethereum / Arbitrum / Base / BSC)**:
  - Honeypot checker: `https://honeypot.is/`
  - Contract audit: `https://tokensniffer.com/`
- **Solana**:
  - Security audit: `https://rugcheck.xyz/`
  - Pair tracking: `https://dexscreener.com/`

---

## 📋 Audit Report Template

```markdown
### 🛡️ On-Chain Security Audit: [TOKEN_SYMBOL]

- **Chain / DEX**: [e.g. Solana / Raydium]
- **Current Price**: [$X.XX]
- **Liquidity Pool (USD)**: [$XXX,XXX]
- **FDV (Fully Diluted Valuation)**: [$X,XXX,XXX]
- **24h Volume**: [$XXX,XXX]

#### ⚠️ Security Check Matrix:
- [x] Liquidity Locked / Burned: [YES / NO / UNKNOWN]
- [x] Mint Authority Revoked: [YES / NO]
- [x] Tax Assessment: [0% Buy / 0% Sell]
- [x] Wash Trading Indicators: [LOW / HIGH]

#### 🎯 Verdict:
**[SAFE FOR TRADING / HIGH RISK CAUTION / AVOID - LIKELY SCAM]**
```
