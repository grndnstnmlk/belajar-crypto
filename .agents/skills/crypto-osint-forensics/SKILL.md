---
name: crypto-osint-forensics
description: Blockchain OSINT, On-Chain Forensic Intelligence, Whale Tracking, Arkham/Nansen Entity Profiling, and Market Maker Inventory Forensics skill. Use when tracking smart money wallet clusters, auditing exchange reserve flows (CEX Inflows/Outflows), profiling market maker manipulation (Wintermute, DWF Labs, Jump), monitoring token unlock vesting cliffs, and detecting insider accumulations.
---

# Crypto OSINT & On-Chain Forensics Playbook
*Blockchain Entity Profiling, Whale Intelligence & Market Maker Forensics*

This skill equips Antigravity AI agents with on-chain forensic investigation workflows, entity clustering techniques, and institutional flow intelligence to decode smart money behavior before it reflects on the public order book.

---

## 🏛️ On-Chain Forensic Architecture

```
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ BLOCKCHAIN DATA FEEDS   │ ───► │ ENTITY CLUSTERING &     │ ───► │ FORENSIC INTEL GRAPH    │
│ - Arkham / Nansen       │      │ WALLET LABELS           │      │ - Whale Net Inflow      │
│ - Etherscan / Solscan   │      │ - Market Makers (MM)    │      │ - CEX Reserve Shifts    │
│ - Debank / GMGN         │      │ - VC Vesting / Whales   │      │ - Insider Cluster Map   │
└─────────────────────────┘      └─────────────────────────┘      └────────────┬────────────┘
                                                                               │
                                 ┌─────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│   ALPHA ACTION DESK     │ ◄─── │ ADVERSARIAL INTEGRATION │ ◄─── │ FORENSIC TRIGGER ALERTS │
│ - Front-run MM Pushes   │      │ - Supply Shock Review   │      │ - CEX Deposit Spike     │
│ - Short Unlock Cliffs   │      │ - Dump Risk Assessment  │      │ - Stealth Accumulation  │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

---

## 🔍 Phase 1: Entity Profiling & Market Maker Tracking

### 1. Key Market Maker Profiles & Behaviors
- **Wintermute / Jump Trading / GSR**:
  - Algorithmic two-sided liquidity provisioning.
  - Inflow to Binance/Bybit spot deposit addresses $\rightarrow$ Imminent volatility expansion or liquidity support.
- **DWF Labs / High-Beta MMs**:
  - Aggressive directional momentum and narrative pushes.
  - Large OTC transfers followed by spot buying waves on perpetual-listed altcoins.

### 2. Exchange Net Flow Forensics
$$\text{Exchange Net Flow} = \text{CEX Inflow Volume} - \text{CEX Outflow Volume}$$

- **Large CEX Inflow Spike ($> \$5\text{M} - \$20\text{M}$)**:
  - Whales moving spot tokens onto centralized exchanges.
  - *Bearish Flag*: High probability of impending market sell orders or OTC settlement dumps.
- **Persistent CEX Outflow**:
  - Tokens moving from Binance/Coinbase into cold storage / multisig vaults.
  - *Bullish Flag*: Supply shock / accumulation phase. Floating liquid supply is contracting.

---

## 🕵️ Phase 2: Whale Clustering & Insider Forensics

### 1. Sybil & Multi-Wallet Clustering
Insiders rarely accumulate from a single address. Detect coordinated cluster behavior:
- **Funding Origin Analysis**: Multiple fresh wallets funded by the same Tornado Cash, Binance hot wallet, or FixedFloat transaction.
- **Synchronized Swap Execution**: Multiple wallets buying the same token within the same block or 10-minute window with identical gas settings.

### 2. Token Unlock & Vesting Cliff Forensics
- **Cliff Unlock Audit**: Cross-reference TokenUnlocks / Tokenomist data with on-chain vesting contracts.
- **Rule**: If a cliff unlock $\ge 3\%$ of circulating supply is scheduled within 72 hours and team/investor addresses initiate test transactions to CEX deposit addresses $\rightarrow$ **Strict Short Bias or Halt Longs**.

---

## 🚨 Phase 3: Forensic Intel Alert Checklist

Before certifying an asset for long-term swing or high-conviction trade tickets:

1. [ ] **Exchange Reserves**: No abnormal spike in exchange deposits over the last 24 hours.
2. [ ] **Top 10 Holder Concentration**: Top 10 non-contract wallets hold $< 40\%$ of circulating supply (excluding liquidity pools and burnt addresses).
3. [ ] **Market Maker Inventory**: MM addresses actively providing balance without net multi-million liquidation outflows.
4. [ ] **Dev / Deployer Balance**: Dev wallet has not dumped tokens into DEX liquidity pools (Zero Rug / HoneyPot risk).
5. [ ] **Smart Money Wallets**: Nansen/GMGN top PnL smart money wallets showing positive 7-day net accumulation.

---

## 🛠️ Integrated Workspace Tools
- `.agents/tools/crypto_osint_forensics_hub.py` — Multi-chain OSINT intelligence hub and entity tracker.
- `.agents/tools/smart_money_tracker.py` — Smart money wallet movement and accumulation detector.
- `.agents/data/osint_forensics_intel.json` — Cached on-chain entity records, flags, and whale flows.
- `.agents/data/osint_graph_export.json` — Network graph of connected cluster entities.
