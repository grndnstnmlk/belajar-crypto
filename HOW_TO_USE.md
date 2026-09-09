# 🤖 Autonomous AI Trading Desk — User Guide & Manual (HOW TO USE)

Panduan operasional lengkap untuk menjalankan, mengendalikan, dan memantau **Autonomous AI Crypto Trading Agent** (Binance Futures Testnet & Live).

---

## 📑 Daftar Isi
1. [Prasyarat & Persiapan Awal](#1-prasyarat--persiapan-awal)
2. [3 Mode Operasional Trading Desk](#2-3-mode-operasional-trading-desk)
3. [Cara Menjalankan Trading Desk (CLI & Batch)](#3-cara-menjalankan-trading-desk-cli--batch)
4. [Pengendalian Jarak Jauh via Telegram Bot](#4-pengendalian-jarak-jauh-via-telegram-bot)
5. [Mission Control Web Dashboard (Port 5000)](#5-mission-control-web-dashboard-port-5000)
6. [Sistem Proteksi Otomatis (Hands-Free Risk Management)](#6-sistem-proteksi-otomatis-hands-free-risk-management)
7. [Skrip Diagnostik & Scanner Mandiri](#7-skrip-diagnostik--scanner-mandiri)

---

## 1. Prasyarat & Persiapan Awal

Pastikan file konfigurasi `.env` telah terisi di direktori utama:

```env
# Binance Futures API (Demo Testnet atau Live)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# Telegram Remote Control & Alerts
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# AI Senior Quant Risk Officer (Opsional: Google Gemini API)
GEMINI_API_KEY=your_gemini_api_key_here
```

> [!TIP]
> Jika Chat ID Telegram Anda belum terhubung, jalankan perintah auto-pairing sekali saja:
> ```powershell
> python .agents/tools/telegram_notifier.py pair
> ```
> Lalu buka bot Telegram Anda dan kirim pesan apa saja (misal: "halo").

---

## 2. 3 Mode Operasional Trading Desk

Trading desk memiliki 3 mode eksekusi yang dapat diganti sewaktu-waktu melalui CLI maupun Telegram:

| Mode | Timeframe | Fokus Strategi | Alokasi Risiko | Target R:R | Karakteristik |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **`SCALP`** | **5m** (Mikro) | 5 Setup Elite Kripto: ICT Rejection Block (50% Mean Threshold), 4H-Range Breakout Re-entry (Fakeout), Inverse FVG (IFVG), 15m Key-Level Rectangle Break & Retest (Mulham), 20-EMA Pullback Trap, Liquidity Sweep | **0.35% – 0.50%** (Micro-Kelly) | **1:1.80 – 1:2.50** | Eksekusi cepat 15–35 menit, Micro-BE (+0.60R), Scale-Out TP1 (+1.25R, 60%), 20-min Anti-Stall Time-Stop |
| **`HYBRID`** *(Default)* | **5m + 1H** | Dual Engine: Menangkap Swing 1H sekaligus Scalp 5m | **0.50% s/d 1.05%** | **1:2.00 – 1:3.50** | Fleksibel: Eksekusi scalp kilat ke slot kosong saat menunggu setup swing matang |
| **`SWING`** | **1H & 4H** (Makro) | SMC, Wyckoff Accumulation, Volume Profile VAH/VAL, FVG Retest | **1.05% – 1.50%** | **1:3.00 – 1:5.00+** | Menunggangi ekspansi tren besar multi-jam/hari, proteksi Chandelier Trailing |

---

## 3. Cara Menjalankan Trading Desk (CLI & Batch)

Buka PowerShell di folder proyek (`c:\Users\USER\Downloads\Githubku\belajar kripto`):

### A. Menjalankan Mode SCALP (Fast Scalper 5m)
```powershell
# 1. Siklus 24/7 Autopilot (Memindai 10 koin teratas setiap 1 menit)
python .agents/tools/trading_desk.py run --mode SCALP --interval 1

# 2. Siklus Uji Coba Sekali Jalan (Single Run Test)
python .agents/tools/trading_desk.py run --mode SCALP --once
```

### B. Menjalankan Mode HYBRID (Swing + Scalp Otomatis)
```powershell
# Berjalan terus-menerus dengan interval 1-2 menit
python .agents/tools/trading_desk.py run --mode HYBRID --interval 1
```

### C. Menjalankan Mode SWING (Tren Besar 1H)
```powershell
# Berjalan terus-menerus dengan interval 15 menit
python .agents/tools/trading_desk.py run --mode SWING --interval 15
```

### D. Mode Demo Testnet vs Live Real Money
* **Demo Testnet (Bebas Risiko)**: Default (tanpa flag tambahan). Menggunakan saldo virtual Binance Futures Testnet.
* **Live Real Money**: Tambahkan argumen `--live`:
  ```powershell
  python .agents/tools/trading_desk.py run --mode HYBRID --interval 1 --live
  ```

### E. Melalui File Batch Windows (.bat)
* Jalankan `start_autopilot.bat` untuk menyalakan daemon desk autopilot.
* Jalankan `start_dashboard.bat` untuk menyalakan Mission Control Web Dashboard.

---

## 4. Pengendalian Jarak Jauh via Telegram Bot

Anda dapat mengendalikan bot secara penuh dari HP tanpa perlu membuka terminal laptop:

```
                  ┌────────────────────────┐
                  │   TELEGRAM BOT REMOTE  │
                  └───────────┬────────────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
[STATUS & INTEL]      [KONTROL MODE]         [EKSEKUSI POSISI]
• /status             • /scalp               • /scaleout (TP 50%)
• /pnl (24h Recap)    • /hybrid              • /close <koin>
• /scalpscan          • /swing               • /closeall
• /rejection          • /pause /resume       • /chart <koin> <tf>
```

### Daftar Perintah Interaktif:

| Perintah | Fungsi | Contoh Respon / Tindakan |
| :--- | :--- | :--- |
| **`/scalpscan`** | ⚡ **Scan 5m Scalp Instan** | Memindai 10 koin teratas detik ini dan mengirim kartu sinyal entry, SL, TP |
| **`/scalp`** | ⚡ **Ganti ke Mode Scalp** | Mengubah operasional desk ke 5m Fast Scalper (Micro-BE +0.6R, Time-Stop 20m) |
| **`/hybrid`** | 🤖 **Ganti ke Mode Hybrid** | Mengaktifkan dual-engine (1H Swing + 5m Scalp bersamaan) |
| **`/swing`** | 🎯 **Ganti ke Mode Swing** | Mengaktifkan mode tren besar 1H/4H (Target R:R $\ge 1:3.0$) |
| **`/rejection`** | 🕯️ **Pantau Rejection Block** | Menampilkan zona Mean Threshold 50% untuk BTC, ETH, dan SOL |
| **`/status`** | 📊 **Cek Saldo & Posisi** | Menampilkan saldo dompet USDT dan daftar posisi aktif dengan floating PnL |
| **`/pnl`** | 💰 **Rangkuman 24 Jam** | Laporan eksekutif: Win Rate, Profit Factor, Net PnL harian |
| **`/chart btc 5m`** | 📈 **Snapshot Chart** | Mengirim gambar grafik candlestick 5m lengkap dengan pita VWAP & target |
| **`/scaleout`** | 🎯 **Amankan Cuan 50%** | Menjual 50% lot di market dan menggeser sisa posisi ke Breakeven |
| **`/close btc`** | 🔴 **Tutup 1 Posisi** | Melikuidasi posisi koin tertentu secara instan di market |
| **`/closeall`** | 🚨 **Tutup Semua Posisi** | Darurat: Melikuidasi seluruh posisi terbuka menjadi kas USDT |
| **`/pause`** | ⏸️ **Jeda Desk** | Menghentikan pembukaan posisi baru |
| **`/resume`** | ▶️ **Lanjutkan Desk** | Melanjutkan pemindaian dan eksekusi autopilot |

---

## 5. Mission Control Web Dashboard (Port 5000)

Mission Control Dashboard menyajikan pemantauan grafis visual secara real-time:
* **Alamat URL**: [http://localhost:5000](http://localhost:5000)

### Tab Dashboard:
1. **Real-Time Feed**:
   * Ticker harga langsung koin-koin likuid.
   * Kartu posisi aktif dengan margin, floating PnL dinamis, dan status exchange.
2. **Chart & Market Intelligence**:
   * Candlestick interaktif TradingView-grade (1m, 5m, 15m, 1H).
   * Overlay Indikator Institusional: Institutional VWAP ($\pm 1\sigma, \pm 2\sigma$), Volume Profile (VAH, POC, VAL), Fair Value Gaps (FVG), dan Rejection Block Zones.
   * **Active Scalp Screener**: Daftar peluang scalping 5m yang sedang aktif di pasar.
3. **Quant Trade Journal**:
   * Metrik performa kuantitatif: *Win Rate*, *Profit Factor*, *Expectancy*, *Payoff Ratio*, dan *Max Drawdown*.
   * Buku besar (*ledger*) riwayat seluruh trade tertutup lengkap dengan rincian komisi fee bursa.

*Jika dashboard belum aktif di background, nyalakan dengan:*
```powershell
python -u .agents/tools/dashboard_server.py
```

---

## 6. Sistem Proteksi Otomatis (Hands-Free Risk Management)

Begitu order terisi di bursa, posisi Anda dikawal 24/7 secara otomatis oleh **Trade Manager** ([trade_manager.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/tools/trade_manager.py)):

1. **Micro-Breakeven (+0.60R)**:
   * Begitu trade scalping mencapai laba $+0.60R$, Stop Loss otomatis digeser ke titik `Entry + 0.08%` (menutup biaya komisi fee). Trade Anda dijamin bebas risiko (*Free Roll*).
2. **Micro Scale-Out TP1 (+1.25R)**:
   * Saat floating profit menyentuh $+1.25R$, bot otomatis menjual **60% dari kuantitas lot** di market untuk mengunci profit kas ke dompet, menyisakan 40% sebagai *runner* dengan proteksi Breakeven.
3. **Strict 20-Minute Anti-Stall Time-Stop**:
   * Jika posisi scalping berjalan selama $\ge 20$ menit (4 candle 5m) dan pergerakan harga stagnan di rentang flat ($0.0 \le R < 0.35$), bot akan menutup posisi di market untuk membebaskan modal margin.
4. **Liquidation Crowd Guard**:
   * Menganalisis Funding Rate dan rasio Long/Short Coinglass. Jika ritel terlalu padat (*crowded longs/shorts*), bot otomatis membatalkan eksekusi untuk melindungi akun dari *liquidation squeeze dump*.
5. **Macro News Blackout Shield**:
   * Otomatis menjeda pembukaan posisi 30 menit sebelum dan sesudah rilis berita ekonomi AS berbobot tinggi (CPI, NFP, FOMC, PPI).
6. **Portfolio Correlation & Directional Heat Guard (Maksimal 4 Posisi)**:
   * **Kapasitas Portofolio**: Maksimal 4 posisi aktif bersamaan (`MAX_TOTAL_POSITIONS = 4`).
   * **Batas Posisi Searah (*Directional Cap*)**: Maksimal 3 posisi searah (misal: 3 Long atau 3 Short). Slot ke-4 dicadangkan khusus untuk Hedging (arah berlawanan) atau Cadangan Kas demi mencegah kerugian serentak (*quadruple-SL*) saat pasar berbalik arah secara drastis.
   * **Cluster Altcoin Guard**: Maksimal 3 *High-Beta Altcoins* bersamaan guna mencegah over-konsentrasi pada token berkorelasi tinggi.
   * **Dynamic Heat Scaling**: Alokasi risiko posisi ke-1 (100%), posisi ke-2 (75%), posisi ke-3 (50%), dan posisi ke-4 (35%) sehingga total risiko terarah kumulatif tetap aman dan terkendali.
7. **Tauric Adversarial Debate Layer (Bull 🐂 vs Bear 🐻)**:
   * Mengadopsi arsitektur multi-agent institusional **Tauric Research** (*TradingAgents*, arXiv:2412.20138).
   * Sebelum order dieksekusi, **Bull Researcher** (katalis kenaikan & struktur FVG) dipertemukan dengan **Bear Researcher** (*Devil's Advocate*, jebakan likuiditas & fakeout) dalam debat dialektika.
   * **Debate Arbiter** menimbang argumen secara objektif terhadap data pasar live:
     * **`APPROVE`**: Bull menang meyakinkan $\rightarrow$ eksekusi ukuran penuh.
     * **`ADJUST_RISK`**: Kompromi kehati-hatian $\rightarrow$ ukuran risiko otomatis dipotong ke 50%.
     * **`VETO`**: Bear mengekspos risiko fatal $\rightarrow$ eksekusi dibatalkan demi proteksi modal.
   * Mendukung mode ganda (*Dual-Engine*): **Cognitive LLM** (Gemini/OpenAI/DeepSeek/Groq) dan **Deterministic Quant Matrix** (< 5ms). Transkrip debat dapat dipantau langsung di tab Market Intelligence dashboard.
8. **Tauric Tri-Perspective Risk Balancing (TradingAgents CRO Protocol)**:
   * Mengadopsi arsitektur tata kelola risiko multi-perspektif **Tauric Research** (*TradingAgents*, arXiv:2412.20138).
   * Setelah setup lolos debat Bull vs Bear, tiga perwira risiko spesialis mengevaluasi kelayakan posisi secara serentak:
     * 🟢 **Aggressive Risk Officer**: Mengevaluasi peluang pertumbuhan alpha & asimetri return ($R:R \ge 2.5$, momentum ADX, keyakinan Bull). Mengusulkan skala modal agresif ($1.0\times - 1.25\times$) dalam batas aman bursa.
     * 🔵 **Neutral Risk Officer**: Menjadi jangkar kuantitatif objektif berbasis *Half-Kelly Criterion* ($f^*$), rasio ekspektasi statistik ($EV$), dan normalisasi volatilitas ATR. Mengusulkan skala proporsional ($0.60\times - 1.0\times$).
     * 🔴 **Conservative Risk Officer**: Menegakkan prinsip preservasi modal (*capital preservation*), mengawasi margin bebas, penumpukan posisi searah (*directional clustering*), dan potensi *tail-risk drawdown*. Mengusulkan pemangkasan defensif ($0.25\times - 0.50\times$) atau VETO total jika risiko melampaui batas aman.
     * 🏛️ **Fund Manager (Chief Risk Officer Synthesis)**: Menimbang ketiga pandangan dengan pembobotan dinamis adaptif (bobot konservatif melonjak ke 60% bila portofolio sedang tertekan), menetapkan skor komposit (0-100), skala alokasi akhir, profil Stop Loss (`ATR_TRAILING`, `TIGHT_BREAKEVEN`, atau `RUNNER_EXPANSION`), serta vonis izin (`APPROVED_OPTIMAL`, `APPROVED_BALANCED`, `APPROVED_DEFENSIVE`, atau `BLOCKED_RISK_LIMIT`).
   * Tersedia visualisasi 3-bar dinamis dan kartu adjudikasi Fund Manager pada tab *Market Intelligence* di Web Dashboard.
9. **Tauric Sentiment & Social Narrative Scanner (TradingAgents Analyst Protocol)**:
   * Mengadopsi pilar *Sentiment & News Analyst* dari framework **Tauric Research** (*TradingAgents*, arXiv:2412.20138) yang disintesis dengan Akademi Crypto Module 01 (Macro Sentiment & Narrative Trading).
   * **Crypto Fear & Greed Index Engine**: Memantau indeks sentimen pasar 0-100 real-time via Alternative.me dengan sinyal institusional kontrarian (*Extreme Fear* < 25 = akumulasi harga diskon institusional; *Extreme Greed* > 75 = waspada *liquidation sweep* dan *retail trap*).
   * **Rotasi Modal 6 Sektor Narasi**: Melacak kinerja 24 jam dan volume bursa di 6 sektor kunci: 🤖 *AI & DePIN*, ⚡ *Solana & Alt-L1*, 🏛️ *RWA & DeFi*, 🐶 *Meme & Cultural Tokens*, ⛓️ *L2 & Modular Rollups*, dan 👑 *Macro Heavyweights*. Setup yang searah dengan sektor pemimpin (#1 Leader) otomatis mendapatkan bonus konfluensi akurasi!
   * **Social Buzz & Virality Index**: Memindai token pencarian terpopuler (*trending search*) global via CoinGecko untuk mendeteksi siklus *organic expansion* vs *retail FOMO climax*.
   * **Dukungan Perintah Telegram**: Ketik `/sentiment` atau `/narrative` di bot Telegram kapan saja untuk menerima laporan sentimen pasar dan rotasi sektor terkini secara instan dari ponsel Anda.

10. **Paperclip Autonomous Trading Firm Architecture & Board Governance**:
    * Terinspirasi dari platform orkestrasi multi-agent **Paperclip AI** ([paperclipai/paperclip](https://github.com/paperclipai/paperclip)), sistem trading dirombak menjadi kantor prop trading otonom dengan struktur hierarki resmi.
    * **Struktur Rantai Komando (Org Chart)**:
      * 👑 **Dewan Direksi (Anda / Manusia)**: Memegang hak veto tertinggi, otorisasi sinyal berisiko tinggi (*Human-In-The-Loop*), dan saklar pemutus darurat (*Circuit Breaker*).
      * 🧠 **Chief Risk Officer & Fund Manager**: Mengawasi seluruh departemen, menyintesis Tri-Perspective Risk, dan mengatur batas margin portofolio.
      * 📊 **Departemen Riset & Intel**: *Market Eyes Screener*, *Sentiment Narrative Scanner*, dan *DEX On-Chain Auditor*.
      * ⚔️ **Departemen Strategi & Debat**: *Bull vs Bear Debaters* dan *Akademi Scalper Specialists* (Mulham, 20 EMA, 4H, Inverse FVG).
      * ⚡ **Desk Eksekusi & Operasi**: *Binance Order Router* dan *Trade Journaler & Autopsy Auditor*.
    * **Papan Delegasi Tiket Tugas (Kanban Pipeline)**: Setiap setup yang terdeteksi dibuatkan tiket unik (`TCK-...`) dan berpindah secara transparan melalui 5 tahap: `DISCOVERED` ➡️ `DEBATING` ➡️ `RISK_AUDIT` ➡️ `PENDING_BOARD` (bila berisiko tinggi) ➡️ `EXECUTED / CLOSED`.
    * **Pintu Otorisasi Dewan Direksi (*Board Approval Gate*)**: Setup yang memicu kriteria risiko ekstrem (portofolio padat $\ge 3$ posisi, *Extreme Fear/Greed*, atau alokasi $\ge 1.25\times$) akan ditahan di tahap `PENDING_BOARD` dan meminta persetujuan manusia via tombol **[SETUJUI] / [TOLAK]** di Web Dashboard atau Telegram (`/board_approve <id>`).
    * **Penjadwalan Heartbeat & Zero-Cost Quota Guard**: Setiap agen bekerja berdasarkan siklus denyut (*heartbeat*) terukur untuk menghemat CPU dan melindungi kuota gratisan Google Gemini (15 RPM / 1.500 req/hari), menjamin operasional **100% Gratis (Rp 0)**.

11. **Order Flow, CVD Divergence & DOM Footprint Micro-Scalping**:
    * **Cumulative Volume Delta (CVD) Engine**: Mengurai setiap transaksi pasar (*market taker orders*) via Binance Futures `aggTrades` untuk mendeteksi tekanan beli/jual agresif secara real-time (`Delta = Taker Buy - Taker Sell`).
    * **Deteksi Institutional Absorption**:
      * 🟢 **Bullish Absorption**: Harga membentuk *Lower Low*, namun CVD membentuk *Higher Low* $\rightarrow$ Sinyal bahwa aksi jual agresif ritel telah diserap penuh oleh limit order institusional (*Smart Money Bids*).
      * 🔴 **Bearish Absorption**: Harga membentuk *Higher High*, namun CVD membentuk *Lower High* $\rightarrow$ Sinyal bahwa aksi beli FOMO ritel sedang ditampung oleh dinding jual institusional (*Smart Money Asks*).
    * **Depth of Market (DOM) Stacked Imbalance**: Memindai kedalaman orderbook L2 50-level untuk mendeteksi dinding likuiditas $\ge 3.0\times$ dominan.
    * **Eksekusi Sinyal Mandiri**: Sinyal `5m Order Flow CVD Absorption Scalp` (Target R:R 1:2.0) langsung masuk antrean eksekusi desk dengan Stop Loss sangat tipis di balik sumbu *absorption*.

---

## 7. Skrip Diagnostik & Scanner Mandiri

Anda dapat menjalankan skrip-skrip independen kapan saja untuk inspeksi cepat:

```powershell
# 1. Pemindai Scalping 5m Kilat (10 Koin)
python .agents/tools/fast_scalper.py

# 2. Analisis Lengkap Intelijen Institusional untuk BTC (atau ETH / SOL)
python .agents/tools/market_eyes.py --symbol BTC

# 3. Deteksi ICT Rejection Block & 50% Mean Threshold
python .agents/tools/rejection_block_engine.py

# 4. Status Portofolio dan Ringkasan Posisi Terbuka
python .agents/tools/trading_desk.py status

# 5. Audit Kesehatan Sistem Total (26 Poin Uji Operasional)
python scratch/total_system_debug.py
```

---

*Dikembangkan dengan standar arsitektur kuantitatif & silabus Akademi Crypto Module 01-04.*
