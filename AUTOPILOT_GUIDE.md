# 🤖 Panduan Lengkap Cara Kerja Autopilot Trading Desk (Hybrid Dual-Engine)
*Dokumentasi Arsitektur Otonom, Multi-Agent Swarm, Risk Guardrail & Eksekusi Binance Futures 20x*

---

## 🏛️ 1. Ikhtisar Sistem (System Overview)

Sistem **Autopilot Trading Desk** adalah mesin trading otonom berbasis *Multi-Agent Swarm Intelligence* yang disintesis dari kurikulum **Akademi Crypto (Modul 01 - 08)**.

Sistem ini beroperasi **24/7 tanpa henti** di latar belakang (*background daemon*), menggabungkan analisis makroekonomi, sinyal teknikal kuantitatif (*Smart Money Concepts* & *Wyckoff*), pembacaan aliran pesanan (*Order Flow* & Level-2 *Depth*), serta pengawalan risiko modal ketat bergaya *Proprietary Trading Firm*.

---

## 🔄 2. Diagram Alur Siklus Otonom (Autonomous 6-Stage Pipeline)

Setiap siklus pemindaian (interval **45–60 detik** pada mode **HYBRID**) mengeksekusi 6 tahapan terstruktur:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FASE 1: PRE-FLIGHT & RISK AUDIT                        │
│   • Sisa Margin Bebas & Saldo          • Macro News Blackout Shield (FOMC/CPI/NFP)    │
│   • Directional Heat (Max Long/Short)  • BTC Macro Regime & Dominance Compass (BTC.D)  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        FASE 2: DUAL-ENGINE OPPORTUNITY DISCOVERY                       │
│   ┌───────────────────────────────────┐    ┌───────────────────────────────────────┐   │
│   │    ⚡ 5m/15m FAST SCALPER DESK    │    │      🎯 1H/4H SWING CONFLUENCE DESK   │   │
│   │  - Micro-SMC (ChoCH / BOS)        │    │  - HTF Top-Down Trend (EMA 50/200)    │   │
│   │  - Opening Range Breakout (ORB)   │    │  - FVG Mitigation & Wyckoff Schematic │   │
│   │  - 20m Anti-Stall Time-Stop       │    │  - Target Runner 1:3.5R - 1:8.0R      │   │
│   └───────────────────────────────────┘    └───────────────────────────────────────┘   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                            FASE 3: INSTITUTIONAL CONFLUENCE FILTER                     │
│   • Institutional Trading Session (London / NY Kill Zones vs Asian Accumulation)       │
│   • Filter Konfluensi Ketat (Skor minimal 75% s/d 85% sesuai sesi pasar)               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      FASE 4: MULTI-PERSPECTIVE & ADVERSARIAL VALIDATION                │
│   • 🐂 vs 🐻 Tauric Adversarial Debate (Bull Conviction vs Bear Devil's Advocate)     │
│   • ⚖️ Tri-Perspective Risk Consensus (Macro Liquidity, Quant Momentum, CRO)          │
│   • 🧲 Level-2 Depth Imbalance (>= 2.5x Bid/Ask Wall) & Delta Sniping                  │
│   • 🔍 On-Chain & OSINT Security Check (Honeypot, CEX Dump Inflow, Vesting Cliffs)     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           FASE 5: EXECUTION & POSITION SIZING                          │
│   • Sizing Matematis: Adaptive Fractional Half-Kelly Criterion (Maks 1.5% - 2.0% Risk) │
│   • Eksekusi Binance Futures 20x Leverage via Limit-Chase (Hemat Fee Taker/Maker)      │
│   • Notifikasi Instan ke Telegram & Dashboard Visual (Port 5000)                       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        FASE 6: DYNAMIC LIFECYCLE MANAGEMENT (24/7)                     │
│   • Proteksi Breakeven Otomatis (BE Lock) saat profit mencapai +1.5R                   │
│   • Smart Pyramiding (+30% lot) saat profit +2.0R tanpa risiko modal tambahan          │
│   • SMC Trailing Stop dinamis mengikuti Higher Lows / Lower Highs                      │
│   • Auto-Sync Git Ledger ke GitHub Repository                                          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 3. Penjelasan Rinci Komponen Sistem

### 🎯 A. Dual-Engine Hybrid Strategy (High-RR & Big-Wave Prioritization)
Mode **HYBRID** telah dioptimalkan secara agresif untuk mengeliminasi *noise* scalping kecil dan memprioritaskan gelombang profit besar:

1. **🏛️ Institutional Swing & Big Wave Engine (1H / 4H Macro Confluence - Top Priority)**:
   - **Prioritas Eksekusi**: Posisi #1 dalam antrean alokasi margin.
   - **Arsenal Strategi Institusional**:
     - **Naked Point of Control (nPOC) Gravity Magnet** ($1:3.5\text{R} - 1:5.0\text{R}$) via Volume Profile.
     - **Open Interest (OI) Divergence & Whale Absorption** ($1:4.0\text{R} - 1:6.0\text{R}$).
     - **Flash Dump Liquidation Dip-Hunter** ($1:4.0\text{R} - 1:5.0\text{R}$) — V-Shape snapback sniper.
     - **SFP (Swing Failure Pattern) Key-Level Stop-Hunt Snatcher** ($1:4.0\text{R} - 1:6.0\text{R}$).
     - **CVD Absorption & Iceberg Wall Detector** ($1:3.5\text{R} - 1:5.0\text{R}$).
     - **Institutional VWAP $\pm 2.5\sigma - 3.0\sigma$ Elasticity** ($1:3.5\text{R} - 1:4.5\text{R}$).
     - **HTF Top-Down Trend** (*EMA 50/200* + *Wyckoff Phase C Spring / Upthrust* + *FVG Mitigation*).
   - **Target Profit**: Gelombang besar pasar (*Big Wave Runners*) dengan rasio $1:3.5\text{R}$ hingga $1:8.0\text{R}+$.
   - **Sizing**: Alokasi penuh $1.5\% - 2.0\%$ modal per trade + Smart Pyramiding $+30\%$ di $+2\text{R}$.

2. **⚡ High-Conviction Fast Scalper Engine (5m / 15m - Selective Sniper Only)**:
   - **Quality Gate**: Seluruh setup mikro dengan R:R $< 1:3.0\text{R}$ otomatis dibuang. Hanya sinyal konveksitas tinggi ($\ge 1:3.0\text{R}$) yang disetujui.
   - **Slot Cap**: Maksimal 2 posisi scalping aktif bersamaan untuk menjaga sisa margin bagi setup Swing.
   - **Sizing Bernilai**: Menggunakan alokasi risiko proporsional penuh ($1.25\% - 1.50\%$) sehingga setiap Take Profit $+3\text{R}$ menghasilkan profit dolar yang signifikan.
   - **Anti-Stall Guard**: Evaluasi otomatis jika harga stagnan dalam 20–45 menit.

---

### 🛡️ B. Guardrails & Filter Keamanan Modal

Sistem menerapkan 5 lapis proteksi risiko institusional sebelum dana dialokasikan:

| Lapisan Keamanan | Modul Terkait | Cara Kerja & Dampak |
| :--- | :--- | :--- |
| **1. Macro News Blackout** | `macro_news_shield.py` | Memantau kalender ekonomi (CPI, FOMC, NFP). Membekukan order baru **$\pm 30\text{ menit}$** di sekitar jadwal rilis berita berbobot tinggi demi mencegah *slippage* liar. |
| **2. Directional Heat Guard** | `portfolio_guard.py` | Menghitung konsentrasi arah portofolio. Membatasi pembukaan posisi satu arah (maks 4–5 Longs/Shorts serentak) untuk mencegah risiko korelasi sistemik. |
| **3. Macro Trend & Dominance Gate** | `market_regime.py` & `dominance_compass.py` | Membaca indeks $\text{BTC.D}$, $\text{USDT.D}$, dan rezim tren BTC. Jika rezim BTC Bearish, sinyal Long Altcoin disaring sangat ketat. |
| **4. Level-2 Depth Sniping** | `orderbook_delta_sniper.py` | Membaca ketebalan *Order Book Depth Imbalance ($\ge 2.5\times$)*. Menempatkan order limit $+0.05\%$ di depan dinding bid institusional. |
| **5. OSINT & On-Chain Security** | `crypto_osint_forensics_hub.py` | Memeriksa likuiditas DEX, risiko *honeypot*, konsentrasi dompet *whale*, serta transfer besar ke alamat deposit CEX spot. |

---

### 🧠 C. Multi-Agent Swarm & Konsensus Risiko

Sebelum sinyal dieksekusi, terjadi proses audit internal antar agen:

1. **Adversarial Tauric Debate (`adversarial_debate.py`)**:
   - **Agen Bull**: Menyusun tesis pembelian berdasarkan struktur pasar dan momentum.
   - **Agen Bear (Devil's Advocate)**: Mencari setiap potensi kegagalan (resistensi HTF, unlock token, overbought CVD).
   - **Ambang Batas**: Order hanya dieksekusi jika skor konsensus akhir **$\ge 75\%$**.

2. **Tri-Perspective Risk Balance (`tri_perspective_risk.py`)**:
   - Menyeimbangkan 3 perspektif risiko (*Aggressive*, *Neutral*, *Conservative*).
   - *Chief Risk Officer (CRO)* menetapkan skala alokasi modal optimal ($0.5\times - 1.0\times$).

---

### 📐 D. Mathematical Position Sizing (Adaptive Half-Kelly)

Penentuan besaran lot tidak menggunakan tebakan, melainkan rumus matematis:

$$f^* = \lambda \cdot \left( \frac{p \cdot b - q}{b} \right)$$

Di mana:
- $p$ = *Win Rate* historis dari jurnal trading.
- $q = 1 - p$ (*Loss Rate*).
- $b$ = *Payoff Ratio* ($\text{Rata-rata Profit} / \text{Rata-rata Loss}$).
- $\lambda = 0.25 - 0.30$ (*Fractional Safety Factor*, membatasi risiko modal maksimal pada **$1.5\% - 2.0\%$** per trade).

---

### 📈 E. Dynamic Trade Lifecycle (Pengawalan Posisi Terbuka)

Setelah posisi aktif di Binance Futures:
- **$+1.5\text{R}$ Floating Profit $\rightarrow$ Breakeven Auto-Lock**: Stop Loss digeser ke Entry $+ 0.1\%$ (menutup biaya transaksi). Posisi berubah menjadi **100% bebas risiko modal (*Risk-Free Trade*)**.
- **$+2.0\text{R}$ Floating Profit $\rightarrow$ Smart Pyramiding**: Menambah ukuran posisi $+30\%$ dengan Stop Loss yang sudah terkunci di atas Breakeven.
- **SMC Dynamic Trailing Stop**: Menjaga keuntungan dengan menarik SL mengikuti *Higher Lows* (pada posisi Long) atau *Lower Highs* (pada posisi Short).

---

## 🎮 4. Cara Penggunaan & Navigasi Operasi

### 🚀 Menjalankan Autopilot
Cukup klik ganda file peluncur di folder utama:
```cmd
start_autopilot.bat
```
Peluncur akan membuka menu interaktif berwarna dan **otomatis menjalankan `[1] HYBRID AUTOPILOT` dalam 5 detik** jika tidak ada tombol ditekan.

---

### 🖥️ Membuka Web Dashboard Visual
Buka peramban (*browser*) Anda ke alamat:
```
http://localhost:5000
```
Dashboard menyajikan:
- Status modal, margin bebas, dan posisi aktif Binance Futures & MT5 secara *real-time*.
- Visualisasi metrik makro, sentimen likuidasi, dan *Order Book Depth*.
- Tombol kendali cepat: **⏸️ Jeda / ▶️ Lanjutkan**, **🎯 Ganti Mode**, dan **🚨 Tutup Semua Posisi**.

---

### 📱 Perintah Kendali Telegram (Two-Way Remote Control)
Bot Telegram terhubung langsung dengan mesin trading. Anda dapat mengirimkan perintah teks kapan saja:

| Perintah | Fungsi |
| :--- | :--- |
| `/status` | 📊 Menampilkan ringkasan saldo, margin, dan seluruh posisi aktif |
| `/pnl` | 💰 Menampilkan rincian profit/loss real-time dan statistik hari ini |
| `/mode` | 🎯 Mengubah mode operasi (*HYBRID*, *SWING*, atau *SCALP*) |
| `/pause` | ⏸️ Menjeda pembukaan order baru (posisi aktif tetap dikawal SL/TP) |
| `/resume` | ▶️ Melanjutkan pemindaian dan eksekusi autopilot |
| `/closeall` | 🚨 Menutup darurat seluruh posisi terbuka di bursa |
| `/ask <pertanyaan>` | 🤖 Konsultasi langsung dengan AI Senior Quant Risk Officer |

---

## 📂 5. Struktur Berkas Kunci Sistem

- [`start_autopilot.bat`](start_autopilot.bat) — Peluncur utama autopilot berkecepatan tinggi.
- [`.agents/tools/trading_desk.py`](.agents/tools/trading_desk.py) — Mesin orkestrator eksekutif trading desk.
- [`.agents/tools/launcher.py`](.agents/tools/launcher.py) — Terminal interaktif dan auto-boot selector.
- [`.agents/tools/dashboard_server.py`](.agents/tools/dashboard_server.py) — Server Web Dashboard (Port 5000).
- [`dashboard.html`](dashboard.html) — Antarmuka web visual *GSAP Animated Chalkboard*.
- [`.agents/data/desk_state.json`](.agents/data/desk_state.json) — Berkas status persisten mode operasional desk.
- [`.agents/data/trade_journal_ledger.json`](.agents/data/trade_journal_ledger.json) — Buku besar jurnal trading otomatis.
