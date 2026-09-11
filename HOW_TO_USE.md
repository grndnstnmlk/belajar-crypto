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
| **`SWING`** *(Default & Rekomendasi)* | **1H & 4H** (Makro) | SMC, Wyckoff Accumulation, Volume Profile VAH/VAL, FVG Retest, Tim Flossbach MSS | **1.05% – 1.50%** (Full Kelly) | **1:3.00 – 1:5.00+** | **Profit Maksimal**: Menunggangi ekspansi tren besar multi-jam/hari, proteksi SMC Trailing (+2R/+3R), tanpa time-stop prematur |
| **`HYBRID`** | **5m + 1H** | Dual Engine: Menangkap Swing 1H sekaligus Scalp 5m | **0.50% s/d 1.05%** | **1:2.00 – 1:3.50** | Fleksibel: Eksekusi scalp kilat ke slot kosong saat menunggu setup swing matang |
| **`SCALP`** | **5m** (Mikro) | 5 Setup Elite Kripto: ICT Rejection Block (50% Mean Threshold), 4H-Range Breakout Re-entry, IFVG, 15m Rectangle Break & Retest | **0.35% – 0.50%** (Micro-Kelly) | **1:1.80 – 1:2.50** | Eksekusi cepat 15–35 menit, Micro-BE (+0.60R), Scale-Out TP1 (+1.25R), 20-min Anti-Stall Time-Stop |

---

## 3. Cara Menjalankan Trading Desk (CLI & Batch)

Buka PowerShell di folder proyek (`c:\Users\USER\Downloads\Githubku\belajar kripto`):

### A. Menjalankan Mode SWING (Tren Besar 1H/4H - Rekomendasi Profit Maksimal)
```powershell
# 1. Siklus Autopilot Terjadwal (Memindai watchlist koin teratas)
python .agents/tools/trading_desk.py run --mode SWING

# 2. Siklus Uji Coba Sekali Jalan (Single Run Test)
python .agents/tools/trading_desk.py run --mode SWING --once
```

### B. Menjalankan Mode HYBRID (Swing + Scalp Otomatis)
```powershell
python .agents/tools/trading_desk.py run --mode HYBRID --interval 1
```

### C. Menjalankan Mode SCALP (Fast Scalper 5m)
```powershell
python .agents/tools/trading_desk.py run --mode SCALP --interval 1
```

### D. Backend Eksekusi: Dual (Binance + MT5), MetaTrader 5, atau Binance Saja
Trading Desk kini mendukung 3 mode eksekusi backend:

* **1. Mode Dual Simultan (`--backend BOTH` - Default Aktif)**:
  * Mengeksekusi order secara bersamaan ke **Binance Futures** dan **MetaTrader 5**.
  * Sizing dihitung otomatis proporsional sesuai modal masing-masing akun (misal: ~$4.6k di Binance USDT + $100k di MT5 Demo).
  ```powershell
  python .agents/tools/trading_desk.py run --mode SWING --backend BOTH
  ```

* **2. MetaTrader 5 Saja (`--backend MT5`)**:
  * Menggunakan saldo virtual `$100,000.00 USD` di terminal MT5.
  * Mendukung multi-aset: **Forex (`EURUSD`, `GBPUSD`)**, **Komoditas (`XAUUSD`/Gold)**, dan **Crypto (`BTCUSD`, `ETHUSD`)**.
  * Pastikan tombol **Algo Trading** di aplikasi MT5 berwarna HIJAU.
  ```powershell
  python .agents/tools/trading_desk.py run --mode SWING --backend MT5
  ```

* **3. Binance Futures Saja (`--backend BINANCE`)**:
  * Mengeksekusi hanya ke akun Binance Futures Demo/Live.
  ```powershell
  python .agents/tools/trading_desk.py run --mode SWING --backend BINANCE
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

## 5. Mission Control Web Dashboard (GSAP Animated Chalkboard Edition)

Mission Control Dashboard menyajikan pemantauan grafis visual secara real-time dengan tema *GSAP Animated Chalkboard* (Dark canvas `#0e100f`, tipe teks krem hangat `#fffce1`, dan taksonomi warna 5-disiplin):
* **Alamat URL**: [http://localhost:5000](http://localhost:5000)

### 4 Ruang Kendali Visual (Tab Navigation):
1. **Terminal (Pintas Keyboard: `1`)**:
   * Candlestick interaktif TradingView-grade (1m, 5m, 15m, 1H).
   * Overlay Indikator Institusional: Institutional VWAP ($\pm 1\sigma, \pm 2\sigma$), Volume Profile (VAH, POC, VAL), Fair Value Gaps (FVG), dan Rejection Block Zones.
   * Kartu posisi aktif dengan margin, floating PnL dinamis, tombol Scale-Out TP1 (50%), Lock Breakeven, dan Darurat Close All.
2. **Market Intelligence (Pintas Keyboard: `2`)**:
   * **Active Scalp Screener**: Daftar peluang scalping 5m yang sedang aktif di pasar.
   * **2D Compass Matrix & Directional Heat**: Visualisasi likuiditas dan eksposur arah portofolio.
   * **Tauric Adversarial Debate Transcripts**: Rekaman dialektika Bull vs Bear sebelum eksekusi.
   * **Tri-Perspective Risk Balancing & Sentiment/Narrative Radar**: Visualisasi skor risiko 3 perwira dan indeks sentimen Fear & Greed.
3. **Trade Journal (Pintas Keyboard: `3`)**:
   * **Filter Cerdas "Hari Ini"**: Langsung memfilter transaksi yang diselesaikan pada tanggal hari ini secara otomatis.
   * **Date Chips Navigator**: Beralih instan antar tanggal historis atau klik *Tampilkan Semua*.
   * **Metrik Performa Dinamis**: *Win Rate*, *Profit Factor*, *Expectancy*, *Payoff Ratio*, dan *Net Realized PnL* yang dihitung secara real-time sesuai tanggal filter yang dipilih.
   * **Tombol Sinkronisasi Binance (`S`)**: Tarik data riwayat trading tertutup terbaru langsung dari Binance Futures API ke buku besar.
4. **Paperclip Firm (Pintas Keyboard: `4`)**:
   * **Org Chart Hierarki Agen**: Visualisasi bagan rantai komando 6 agen institusional.
   * **Kanban Board Tiket**: Melacak siklus tiket dari *Discovered*, *Debating*, *Risk Audit*, hingga *Executed*.
   * **Otorisasi Dewan Direksi (Pending Board)**: Tombol interaktif untuk Menyetujui atau Menolak tiket trade leverage tinggi dengan konfirmasi langsung ke bursa.
   * **Saklar Darurat (Circuit Breaker)**: Tombol jeda darurat terpusat untuk seluruh agen.

### ⌨️ Pintas Keyboard (Global Shortcuts):
* `1` / `2` / `3` / `4` : Berpindah antar tab Terminal, Intel, Journal, dan Firm.
* `R` : Segarkan data grafik candlestick klines & VWAP.
* `S` : Sinkronisasi data trade riwayat tertutup dari Binance Futures.
* `A` : Buka asisten AI Senior Quant Officer Co-Pilot.
* `B` : Buka jendela simulasi kuantitatif Backtest.
* `?` : Buka cheatsheet pintas keyboard lengkap.
* `ESC` : Menutup seluruh dialog modal / popup aktif.

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
    * **Papan Delegasi Tiket Tugas (Kanban Pipeline)**: Setiap setup yang terdeteksi dibuatkan tiket unik (`TCK-...`) dan berpindah secara transparan melalui alur: `DISCOVERED` ➡️ `DEBATING` ➡️ `RISK_AUDIT` ➡️ `AUTONOMOUS_BOARD_APPROVAL` ➡️ `EXECUTED / CLOSED`.
    * **Pendelegasian 100% Autopilot Otonom (Hands-Free Board Governance)**: Seluruh eskalasi otorisasi kini dipasrahkan 100% ke Komite Eksekutif AI (*Autonomous AI Board & Chief Risk Officer*). Sinyal bernilai tinggi diaudit dan disetujui secara otomatis tanpa menahan (*pending/halt*) eksekusi order ke bursa, sehingga bot dapat trading bebas hambatan secara non-stop 24/7.
    * **Penjadwalan Heartbeat & Zero-Cost Quota Guard**: Setiap agen bekerja berdasarkan siklus denyut (*heartbeat*) terukur untuk menghemat CPU dan melindungi kuota gratisan Google Gemini (15 RPM / 1.500 req/hari), menjamin operasional **100% Gratis (Rp 0)**.

11. **Order Flow, CVD Divergence & DOM Footprint Micro-Scalping**:
    * **Cumulative Volume Delta (CVD) Engine**: Mengurai setiap transaksi pasar (*market taker orders*) via Binance Futures `aggTrades` untuk mendeteksi tekanan beli/jual agresif secara real-time (`Delta = Taker Buy - Taker Sell`).
    * **Deteksi Institutional Absorption**:
      * 🟢 **Bullish Absorption**: Harga membentuk *Lower Low*, namun CVD membentuk *Higher Low* $\rightarrow$ Sinyal bahwa aksi jual agresif ritel telah diserap penuh oleh limit order institusional (*Smart Money Bids*).
      * 🔴 **Bearish Absorption**: Harga membentuk *Higher High*, namun CVD membentuk *Lower High* $\rightarrow$ Sinyal bahwa aksi beli FOMO ritel sedang ditampung oleh dinding jual institusional (*Smart Money Asks*).
    * **Depth of Market (DOM) Stacked Imbalance**: Memindai kedalaman orderbook L2 50-level untuk mendeteksi dinding likuiditas $\ge 3.0\times$ dominan.
    * **Eksekusi Sinyal Mandiri**: Sinyal `5m Order Flow CVD Absorption Scalp` (Target R:R 1:2.0) langsung masuk antrean eksekusi desk dengan Stop Loss sangat tipis di balik sumbu *absorption*.

12. **5m/15m Opening Range Breakout (ORB V4.1) Momentum Scalper**:
    * **Konsep TradeX Labs & Akademi Crypto Session Liquidity**: Mengkapitalisasi ledakan volatilitas dan momentum ekspansi harga setelah jendela penemuan harga 15 menit pertama (*Opening Range Discovery Window*) pada pembukaan sesi global.
    * **Jadwal Sesi Utama (WIB)**:
      * 🇬🇧 **London Open ORB**: 14:00 - 14:15 WIB (07:00 UTC) $\rightarrow$ Hunting Window: 14:15 - 15:30 WIB.
      * 🇺🇸 **New York Early / US Pre-Market ORB**: 19:30 - 19:45 WIB $\rightarrow$ Hunting Window: 19:45 - 21:00 WIB.
      * 🇺🇸 **Wall Street Cash Open ORB**: 20:30 - 20:45 WIB $\rightarrow$ Hunting Window: 20:45 - 22:00 WIB.
      * 🌐 **Daily Crypto 00:00 UTC Open ORB**: 07:00 - 07:15 WIB $\rightarrow$ Hunting Window: 07:15 - 08:30 WIB.
      * 🔄 **Dynamic Rolling 15m Inter-Session Fallback**: Memindai konsolidasi 15m dinamis saat di luar jam sesi utama.
    * **Aturan Sinyal & Eksekusi**:
      * 🟢 **Bullish ORB Breakout**: Body candle 5m ditutup tegas di atas $OR_{High}$ + Order Flow CVD Delta Positif $\rightarrow$ **LONG** (Target 1:2.0 R:R). Stop Loss diletakkan di $OR_{Mid}$ (Midpoint) atau sumbu terendah candle penembus.
      * 🔴 **Bearish ORB Breakdown**: Body candle 5m ditutup tegas di bawah $OR_{Low}$ + Order Flow CVD Delta Negatif $\rightarrow$ **SHORT** (Target 1:2.0 R:R). Stop Loss diletakkan di $OR_{Mid}$ atau sumbu tertinggi candle penembus.
    * **Prop Firm Safety Guard**: Maksimal 1 trade per sesi per aset koin (`1 Trade / Session / Symbol`) untuk mencegah over-trading saat pasar berkonsolidasi.

13. **Nautilus Pre-Trade Risk Engine & Research-to-Live Parity**:
    * Terinspirasi dari arsitektur platform kuantitatif kelas institusional **Nautilus Trader** (`nautechsystems/nautilus_trader`).
    * **Pre-Trade Gatekeeper (< 1ms Verification)**: Sebelum order dikirim ke API Binance, sistem secara otonom memvalidasi 5 pilar keselamatan modal:
      1. 🛡️ **Bid/Ask Spread Guard**: Membatalkan order jika spread pasar $> 0.05\%$ (5 bps) untuk mencegah penalti likuiditas.
      2. 🚨 **Daily Drawdown Circuit Breaker**: Mengunci entri baru otomatis jika kerugian harian mencapai $\ge 15.0\%$ dari ekuitas akun.
      3. 💼 **Margin Headroom & Liquidity Buffer**: Memastikan rasio margin bebas akun $\ge 30\%$ sebelum sizing dihitung.
      4. ⚖️ **Expected Slippage Estimator**: Mengestimasi dampak pasar (*market impact*) terhadap ketebalan orderbook L2.
      5. 🌐 **Multi-Asset Directional Cap**: Menjaga batas maksimal 3 altcoin high-beta searah demi mencegah kerugian serentak.
    * **High-Fidelity Research-to-Live Parity Backtest**: Modul backtesting kini mensimulasikan biaya bursa nyata (Binance Taker 0.05%, Maker 0.02%), estimasi slippage (0.025%), dan biaya *funding rate* 8 jam. Hasil backtest 100% mencerminkan profit bersih nyata (*Net Realized Return*) tanpa bias curve-fitting!

14. **Autonomous Agent Memory & Cognitive Reflection Engine**:
    * Disintesis dari arsitektur persistent memory modern **`rohitg00/agentmemory`** untuk mengatasi amnesia lintas-sesi pada AI Trading Agent.
    * **Multi-Tier Memory Architecture**:
      * 📜 **Episodic Trade Memory**: Menyimpan riwayat setup perdagangan, autopsi akar penyebab (*Root Cause*), dan kaidah pelajaran (*Lessons Learned*) setiap kali posisi ditutup (*WIN / LOSS / BE*).
      * 🪙 **Coin Personality Knowledge Graph**: Profiling kebiasaan spesifik per koin (misal: *Wick Risk Rating*, sensitivitas *Funding Rate*, bias *False Breakout*, dan setup SMC optimal).
      * 🛡️ **Tactical Heuristic Rules**: Kaidah taktis dinamis seperti *Macro News Blackout Shield* dan *Funding Crowding Trap Guard*.
    * **High-Speed Hybrid Retrieval (< 2ms)**:
      * Menggabungkan pencarian kata kunci BM25 dengan *Semantic TF-IDF Cosine Similarity* untuk mencocokkan setup saat ini dengan riwayat masa lalu secara instan.
    * **Ebbinghaus Memory Decay**:
      * Menerapkan pembobotan waktu $w(t) = e^{-\Delta t / \tau} \times \text{importance}$ (Half-Life $\tau = 30\text{ hari}$) agar dinamika rezim pasar yang sudah basi meluruh secara alami, sementara pelajaran fundamental tetap abadi.
    * **Pre-Trade Memory Recall**:
      * Sebelum entry order, agen secara otonom memanggil memori historis. Jika setup yang sama berulang kali terkena SL pada rezim koin tersebut, *multiplier* risiko dipangkas secara otomatis (0.5x - 0.85x) untuk melindungi portofolio.
    * **Web Viewer & Keyboard Shortcut**:
      * Tekan <kbd>5</kbd> di dashboard atau klik tab **🧠 Agent Memory** untuk melihat bank memori, metrik retensi, profil koin, dan menjalankan uji refleksi kognitif interaktif.

15. **OpenViking Hierarchical Tiered Context Engine (`L0/L1/L2`)**:
    * Terinspirasi oleh filosofi context-tiering dari **OpenViking** (`openviking.ai` by ByteDance/Volcengine) untuk mengeliminasi LLM token bloat (>90% token reduction) dan mencapai pemuatan konteks kognitif sub-detik (<5ms).
    * **Hierarki Konteks 3 Lapis**:
      * ⚡ **L0 (< 50 tokens) — Ultra-Compact Metadata Header**: Digunakan untuk loop eksekusi cepat frekuensi tinggi (`symbol`, `retention_score`, `total_memories`, `active_rules_count`).
      * 🧠 **L1 (< 150 tokens) — Tactical Heuristic Synopsis**: Digunakan untuk prompt AI Co-Pilot & Risk Officer harian. Menyajikan *Cognitive Multiplier*, *Coin Personality Profile*, dan *Top-3 Relevant Lessons* tanpa membanjiri jendela token.
      * 📚 **L2 (Full Context) — Deep Analytical Audit**: Digunakan untuk audit investigasi penuh, autopsi mendalam paska-likuidasi, dan backtesting kuantitatif komprehensif.
    * **Integrasi 3 Pilar Inti Bersih**:
      1. 🎯 **Pilar 1 (`market_radar.py`)**: Pemindaian pasar multi-indikator single-pass (<5ms) dengan cache kline cerdas (10s TTL).
      2. 🛡️ **Pilar 2 (`nautilus_risk_engine.py`)**: Gatekeeper risiko pra-eksekusi, drawdown circuit breaker, dan adaptive Kelly sizing.
      3. 🧠 **Pilar 3 (`agent_memory_engine.py`)**: Episodic trade memory & refleksi kognitif hierarkis OpenViking.
    * **API Endpoint Terbuka**:
16. **Scientific Quant Volatility & FRED Macro Intelligence Integration**:
    * Terinspirasi oleh standar **`k-dense-ai/scientific-agent-skills`** (`agentskills.io` / `agent-plugins.org`) untuk memperkuat riset kuantitatif saintifik & intelijen likuiditas makro.
    * **Pilar Makro Global (`fred_macro_intel.py`)**:
      * Memantau *Dollar Index (DXY)*, *US 10-Year Treasury Yield*, dan *Federal Reserve Net Liquidity*.
      * Mengkalkulasi *Macro Multiplier* (0.85x – 1.20x) untuk modulasi sizing trading otomatis.
      * Endpoint: `GET /api/macro/fred`.
    * **Pilar Kuantitatif Deret Waktu (`timeseries_quant_forecaster.py`)**:
      * **Parkinson High-Low Volatility**: Estimasi volatilitas berbasis jalur harga kontinu yang jauh lebih akurat untuk pasar kripto frekuensi tinggi.
      * **Value-at-Risk (VaR 95% & VaR 99%)** dan **Expected Shortfall (CVaR)**: Kalkulasi risiko ekor (*tail risk*) parametrik dan empiris.
      * **Dynamic Stop-Loss Buffer**: Mengalibrasi jarak penyangga *structural stop* berdasarkan rezim volatilitas aset saat ini.
      * Endpoint: `GET /api/quant/volatility?symbol=BTC&bar=1h`.
    * **Agent Skill Standard (`.agents/skills/crypto-quant-macro/SKILL.md`)**:
      * Tersedia sebagai plugin skill berstandar internasional yang dapat dipanggil langsung oleh AI Agent.

17. **Multi-Source Market Data Fallback Adapter (Zero Single-Point-of-Failure)**:
    * Terinspirasi oleh direktori kurasi API publik global **`public-apis/public-apis`** untuk memberikan redundansi data bursa tingkat tinggi (*High Availability*).
    * **Hierarki Failover Kripto 3 Lapis**:
      1. 🥇 **Primary**: Binance Public Vision Gateway (`data-api.binance.vision`).
      2. 🥈 **Secondary 1**: CoinPaprika Public Free API (`api.coinpaprika.com` - No Auth).
      3. 🥉 **Secondary 2**: CoinGecko Free API (`api.coingecko.com`).
      4. 🛡️ **Deterministic Memory Baseline**: Jika seluruh koneksi eksternal terputus.
    * **Forex & Stablecoin Peg Monitor (Frankfurter API)**:
      * Mengambil kurs USD/EUR/GBP langsung dari Bank Sentral Eropa (ECB) via *Frankfurter Open API*.
    * **In-Memory Cache (15s TTL)**:
      * Mencegah pemblokiran *rate-limit* dengan eksekusi kueri berlatensi rendah (< 400ms).
    * **Endpoint REST Terbuka**:
      * `GET /api/adapter/multisource?symbol=BTC` — Mengembalikan harga konsensus, jejak failover (*failover trace*), dan metrik latensi.

---

## 7. Skrip Diagnostik & Scanner Mandiri

Anda dapat menjalankan skrip-skrip independen kapan saja untuk inspeksi cepat:

```powershell
# 1. Pemindai Scalping 5m Kilat (10 Koin)
python .agents/tools/fast_scalper.py

# 2. Pemindai Opening Range Breakout (ORB V4.1) untuk BTC / ETH / SOL
python .agents/tools/orb_scalper.py BTC

# 3. Analisis Lengkap Intelijen Order Flow CVD & DOM Footprint
python .agents/tools/orderflow_cvd_scalper.py BTC

# 4. Analisis Lengkap Intelijen Institusional untuk BTC (atau ETH / SOL)
python .agents/tools/market_eyes.py --symbol BTC

# 5. Deteksi ICT Rejection Block & 50% Mean Threshold
python .agents/tools/rejection_block_engine.py

# 6. Status Portofolio dan Ringkasan Posisi Terbuka
python .agents/tools/trading_desk.py status

# 7. Audit Kesehatan Sistem Total (43 Poin Uji Operasional)
python scratch/total_system_debug.py
```

---

*Dikembangkan dengan standar arsitektur kuantitatif & silabus Akademi Crypto Module 01-04.*
