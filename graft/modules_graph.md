# Belajar Kripto — Module Dependency & Function Catalog (Graft)

This catalog enumerates all **78 modules**, their exported functions, classes, and internal dependency links.

---

## `adaptive_indicators.py`
- **File Path**: [`.agents/tools/adaptive_indicators.py`](file:///.agents/tools/adaptive_indicators.py)
- **Summary**: adaptive_indicators.py - Adaptive Technical Indicators & Volatility Modulation Engine Synthesized from Trading Strategies Academy (trading-strategies.academy): 1. Adaptive RSI (ATR-normalized dynamic lookback period) 2. Kaufman Adaptive Moving Average (KAMA / Efficiency Ratio) 3. Dynamic Volatility Regime Classifier
- **Lines**: 230 | **Size**: 8,712 bytes
- **Imports (Outbound)**: [`binance_client.py`](#binance_clientpy)
- **Imported By (Inbound)**: [`market_eyes.py`](#market_eyespy), [`trading_desk.py`](#trading_deskpy)
- **Functions (5)**: `compute_atr()`, `compute_traditional_rsi()`, `compute_adaptive_rsi()`, `compute_kama()`, `get_adaptive_market_intelligence()`

---

## `adaptive_ml_engine.py`
- **File Path**: [`.agents/tools/adaptive_ml_engine.py`](file:///.agents/tools/adaptive_ml_engine.py)
- **Summary**: Adaptive Rolling Machine Learning & Out-of-Distribution (OOD) Anomaly Detector Inspired by FreqAI Dissimilarity Index (DI) and Institutional Scientific Quant Methods. Features: - Multi-Scale Technical Feature Extraction (Returns, Volatility, Volume Flow, EMAs, CVD Proxy). - Mahalanobis Distance & Regularized Covariance Dissimilarity Index (DI). - Three-Tier Anomaly Gate: IN_DISTRIBUTION (1.0x), DISTRIBUTION_DRIFT (0.5x), ANOMALY_OUT_OF_BOUNDS (0.0x / Block). - Rolling L2-Regularized Directional Classifier & Return Forecaster (bps). - Auto-Persistence & 24h Rolling Retraining Pipeline.
- **Lines**: 506 | **Size**: 18,813 bytes
- **Imports (Outbound)**: [`market_eyes.py`](#market_eyespy), [`quant_backtester.py`](#quant_backtesterpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`nautilus_risk_engine.py`](#nautilus_risk_enginepy)
- **Functions (8)**: `extract_candle_features()`, `compute_mean_and_cov_inv()`, `calculate_dissimilarity_index()`, `train_directional_classifier()`, `train_and_cache_model()`, `load_model()`, `evaluate_live_market_ml()`, `audit_pre_trade_ml_safety()`

---

## `adversarial_debate.py`
- **File Path**: [`.agents/tools/adversarial_debate.py`](file:///.agents/tools/adversarial_debate.py)
- **Summary**: Adversarial Debate Layer (Bull vs Bear Agent) Inspired by Tauric Research's TradingAgents Multi-Agent Framework (arXiv:2412.20138) Adapted for 24/7 Autonomous Crypto Trading & Execution.
- **Lines**: 389 | **Size**: 16,795 bytes
- **Imports (Outbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy), [`sentiment_narrative_scanner.py`](#sentiment_narrative_scannerpy)
- **Imported By (Inbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy), [`dashboard_server.py`](#dashboard_serverpy)
- **Functions (5)**: `load_debate_history()`, `save_debate_record()`, `run_deterministic_debate()`, `run_llm_adversarial_debate()`, `run_adversarial_debate()`

---

## `agent_memory_engine.py`
- **File Path**: [`.agents/tools/agent_memory_engine.py`](file:///.agents/tools/agent_memory_engine.py)
- **Summary**: agent_memory_engine.py - Autonomous Persistent Memory & Cognitive Reflection Engine Synthesized from rohitg00/agentmemory institutional memory architecture for Belajar Kripto.
- **Lines**: 1106 | **Size**: 51,650 bytes
- **Imports (Outbound)**: [`atomic_json_store.py`](#atomic_json_storepy)
- **Imported By (Inbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy), [`dashboard_server.py`](#dashboard_serverpy), [`fomo_smc_engine.py`](#fomo_smc_enginepy), [`local_cognitive_brain.py`](#local_cognitive_brainpy), [`nautilus_risk_engine.py`](#nautilus_risk_enginepy), [`trade_journal.py`](#trade_journalpy)
- **Classes**:
  - `class AgentMemoryEngine` (Methods: __init__, load_memories, save_memories, calculate_memory_weight, _tokenize, hybrid_search, get_or_create_coin_profile, sync_with_trade_journal, query_pre_trade_context, reflect_on_closed_trade, get_memory_summary, get_tiered_context, format_prompt_context)

---

## `agent_reach_scanner.py`
- **File Path**: [`.agents/tools/agent_reach_scanner.py`](file:///.agents/tools/agent_reach_scanner.py)
- **Summary**: Agent Reach Intelligence Engine Synthesized from Agent Reach (https://github.com/Panniantong/agent-reach) and Akademi Crypto Market Intelligence architecture.
- **Lines**: 136 | **Size**: 4,539 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Functions (4)**: `fetch_url_markdown()`, `scan_reddit_feed()`, `scan_crypto_news_feed()`, `get_social_intelligence_digest()`

---

## `ai_risk_officer.py`
- **File Path**: [`.agents/tools/ai_risk_officer.py`](file:///.agents/tools/ai_risk_officer.py)
- **Summary**: AI Senior Quant Risk Officer & Autonomous Co-Pilot Synthesizes Akademi Crypto Curriculum (Macro, SMC, Order Flow, and Money Management) with LLM Cognitive Reasoning (Google Gemini, OpenAI, DeepSeek, Groq, or Algorithmic Fallback).
- **Lines**: 905 | **Size**: 41,051 bytes
- **Imports (Outbound)**: [`adversarial_debate.py`](#adversarial_debatepy), [`agent_memory_engine.py`](#agent_memory_enginepy), [`coinglass_derivatives.py`](#coinglass_derivativespy), [`local_cognitive_brain.py`](#local_cognitive_brainpy), [`macro_liquidity.py`](#macro_liquiditypy), [`market_regime.py`](#market_regimepy), [`sentiment_narrative_scanner.py`](#sentiment_narrative_scannerpy), [`tri_perspective_risk.py`](#tri_perspective_riskpy)
- **Imported By (Inbound)**: [`adversarial_debate.py`](#adversarial_debatepy), [`dashboard_server.py`](#dashboard_serverpy), [`sentiment_narrative_scanner.py`](#sentiment_narrative_scannerpy), [`telegram_notifier.py`](#telegram_notifierpy), [`trade_manager.py`](#trade_managerpy), [`trading_desk.py`](#trading_deskpy), [`tri_perspective_risk.py`](#tri_perspective_riskpy)
- **Functions (10)**: `parse_env()`, `get_ai_credentials()`, `call_llm()`, `heuristic_quant_audit()`, `audit_trade_setup()`, `perform_trade_autopsy()`, `answer_trader_query()`, `fetch_klines_for_sentinel()`, `calculate_fast_rsi()`, `evaluate_active_position_exit()`

---

## `atomic_json_store.py`
- **File Path**: [`.agents/tools/atomic_json_store.py`](file:///.agents/tools/atomic_json_store.py)
- **Summary**: atomic_json_store.py - High-Performance Cross-Thread Atomic Transactional JSON Store Provides thread-safe, crash-resilient JSON reads and writes with zero file corruption.
- **Lines**: 131 | **Size**: 4,887 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`agent_memory_engine.py`](#agent_memory_enginepy), [`trade_journal.py`](#trade_journalpy), [`trade_manager.py`](#trade_managerpy)
- **Functions (4)**: `_get_file_lock()`, `atomic_read_json()`, `atomic_write_json()`, `atomic_update_json()`

---

## `auto_git_sync.py`
- **File Path**: [`.agents/tools/auto_git_sync.py`](file:///.agents/tools/auto_git_sync.py)
- **Summary**: auto_git_sync.py - Seamless Multi-Device Git Cloud Synchronization Engine Enables automatic real-time sync between Laptop and PC for trading journals, active positions, and genome state.
- **Lines**: 138 | **Size**: 4,778 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`launcher.py`](#launcherpy), [`trade_journal.py`](#trade_journalpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (5)**: `sync_pull()`, `_do_push()`, `trigger_background_push()`, `_periodic_sync_worker()`, `start_periodic_sync_daemon()`

---

## `backtest_engine.py`
- **File Path**: [`.agents/tools/backtest_engine.py`](file:///.agents/tools/backtest_engine.py)
- **Summary**: Institutional Quantitative Alpha Engine & Multi-Strategy Backtester (Qanat-Inspired DAG) Synthesized with Akademi Crypto (SMC, Fair Value Gap, Market Regime Gatekeeper, and AI Dynamic Exit Sentinel).
- **Lines**: 774 | **Size**: 32,921 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Functions (11)**: `fetch_klines()`, `fetch_synchronized_data()`, `calculate_ema_series()`, `calculate_rsi_series()`, `calculate_dmi_adx_series()`, `run_backtest_simulation()`, `render_ascii_sparkline()`, `display_single_report()`, `run_mode_comparison()`, `run_portfolio_benchmark()`, `main()`

---

## `benchmark_alpha_tracker.py`
- **File Path**: [`.agents/tools/benchmark_alpha_tracker.py`](file:///.agents/tools/benchmark_alpha_tracker.py)
- **Summary**: benchmark_alpha_tracker.py - Agent vs Buy-and-Hold Baseline Alpha Engine Inspired by Open-Finance-Lab/AgenticTrading (create_agent_vs_baseline_leaderboard.py).
- **Lines**: 135 | **Size**: 5,567 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy)
- **Functions (2)**: `load_trade_ledger()`, `calculate_alpha_metrics()`

---

## `binance_client.py`
- **File Path**: [`.agents/tools/binance_client.py`](file:///.agents/tools/binance_client.py)
- **Summary**: Binance Demo & Live Futures Trading Client (Multi-Account Enabled) Supports Binance Futures Testnet (Demo Trading) & Live USDⓈ-M Futures. Bypasses regional SSL blocks via native HTTPS HMAC-SHA256 engine.
- **Lines**: 980 | **Size**: 46,185 bytes
- **Imports (Outbound)**: [`binance_ws_stream.py`](#binance_ws_streampy), [`telegram_notifier.py`](#telegram_notifierpy)
- **Imported By (Inbound)**: [`adaptive_indicators.py`](#adaptive_indicatorspy), [`dashboard_server.py`](#dashboard_serverpy), [`dex_futures_bridge.py`](#dex_futures_bridgepy), [`liquidity_heatmap.py`](#liquidity_heatmappy), [`market_structure.py`](#market_structurepy), [`portfolio_beta_hedger.py`](#portfolio_beta_hedgerpy), [`pyramid_runner_engine.py`](#pyramid_runner_enginepy), [`telegram_notifier.py`](#telegram_notifierpy), [`trade_journal.py`](#trade_journalpy), [`trade_manager.py`](#trade_managerpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (23)**: `sanitize_email_suffix()`, `parse_env_file()`, `resolve_credentials()`, `get_server_time_offset()`, `get_exchange_info()`, `send_signed_request()`, `check_balance()`, `get_ticker()`, `get_realtime_mark_price()`, `set_leverage()`, `get_positions()`, `get_precision_from_step()` *(+ 11 more)*

---

## `binance_ws_stream.py`
- **File Path**: [`.agents/tools/binance_ws_stream.py`](file:///.agents/tools/binance_ws_stream.py)
- **Summary**: Native Binance Futures WebSocket Streaming Engine (< 50ms) Maintains a persistent socket connection to Binance Futures Mark Price & Ticker streams. Maintains in-memory thread-safe state of all crypto pairs for ultra-low-latency O(1) lookups. Features automatic reconnect with exponential backoff, ping/pong heartbeats, and fail-safe REST fallbacks.
- **Lines**: 368 | **Size**: 14,103 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`binance_client.py`](#binance_clientpy), [`dashboard_server.py`](#dashboard_serverpy), [`fast_scalper.py`](#fast_scalperpy), [`htf_macro_lock.py`](#htf_macro_lockpy), [`local_cognitive_brain.py`](#local_cognitive_brainpy), [`market_eyes.py`](#market_eyespy), [`orderbook_delta_sniper.py`](#orderbook_delta_sniperpy), [`trade_manager.py`](#trade_managerpy), [`trading_desk.py`](#trading_deskpy)
- **Classes**:
  - `class BinanceWebSocketStream` (Methods: __init__, _on_open, _on_message, _on_error, _on_close, _run_loop, start, stop)
- **Functions (9)**: `start_stream()`, `stop_stream()`, `get_mark_price()`, `get_funding_rate()`, `get_all_mark_prices()`, `get_book_ticker()`, `get_best_bid_ask()`, `get_all_book_tickers()`, `get_stream_health()`

---

## `chart_snapshot.py`
- **File Path**: [`.agents/tools/chart_snapshot.py`](file:///.agents/tools/chart_snapshot.py)
- **Summary**: Institutional Candlestick Chart Snapshot Generator & Telegram Photo Dispatcher Generates high-resolution, dark-mode TradingView-style chart snapshots with: - Crisp Candlesticks (Green #00c087 / Red #ff4d6a) - Institutional VWAP Curve - Horizontal Entry, Stop Loss, and Take Profit levels with Risk/Reward shaded zones - Sends visual chart snapshots directly to Telegram via official sendPhoto API.
- **Lines**: 398 | **Size**: 16,316 bytes
- **Imports (Outbound)**: [`market_eyes.py`](#market_eyespy), [`telegram_notifier.py`](#telegram_notifierpy)
- **Imported By (Inbound)**: [`telegram_notifier.py`](#telegram_notifierpy)
- **Functions (5)**: `fetch_candles_for_snapshot()`, `compute_vwap()`, `sanitize_chart_text()`, `generate_trade_chart()`, `send_telegram_photo()`

---

## `code_reviewer_runner.py`
- **File Path**: [`.agents/tools/code_reviewer_runner.py`](file:///.agents/tools/code_reviewer_runner.py)
- **Summary**: Alibaba OpenCodeReview & Vercel Skills Automated Workflow Helper Executes diff audits, directory scans, and skill management commands for the Belajar Kripto Workstation.
- **Lines**: 53 | **Size**: 1,862 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Functions (3)**: `run_ocr_review()`, `run_ocr_scan()`, `list_installed_skills()`

---

## `coinbase_premium.py`
- **File Path**: [`.agents/tools/coinbase_premium.py`](file:///.agents/tools/coinbase_premium.py)
- **Summary**: Coinbase Institutional Premium Index Engine Measures real-time price divergence between Coinbase Pro (US Institutional / Wall Street Spot) and Binance/OKX (Global Retail / Offshore Crypto).
- **Lines**: 206 | **Size**: 7,651 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`session_filter.py`](#session_filterpy), [`telegram_notifier.py`](#telegram_notifierpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (5)**: `clean_coin()`, `fetch_json()`, `get_coinbase_premium()`, `get_all_premiums()`, `format_telegram_report()`

---

## `coinglass_derivatives.py`
- **File Path**: [`.agents/tools/coinglass_derivatives.py`](file:///.agents/tools/coinglass_derivatives.py)
- **Summary**: CoinGlass & Coinalyze Institutional Derivatives Intelligence Engine Provides real-time Open Interest, Long/Short Ratio, Predicted Funding Rate, and Multi-Exchange Liquidation Risk metrics.
- **Lines**: 671 | **Size**: 29,058 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy), [`dashboard_server.py`](#dashboard_serverpy), [`market_eyes.py`](#market_eyespy), [`market_radar.py`](#market_radarpy), [`soros_reflexivity_engine.py`](#soros_reflexivity_enginepy), [`telegram_notifier.py`](#telegram_notifierpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (9)**: `clean_coin()`, `fetch_json()`, `get_coinglass_api_key()`, `get_coinalyze_api_key()`, `get_approx_price()`, `get_derivatives_intelligence()`, `format_telegram_report()`, `evaluate_liquidation_hunt()`, `get_oi_archetype_and_liquidation_magnets()`

---

## `crypto_automation_strategies.py`
- **File Path**: [`.agents/tools/crypto_automation_strategies.py`](file:///.agents/tools/crypto_automation_strategies.py)
- **Summary**: crypto_automation_strategies.py - 24/7 Institutional Crypto Autopilot Strategy Engines Specialized for automated hands-free crypto futures trading:
- **Lines**: 419 | **Size**: 17,974 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`fomo_smc_engine.py`](#fomo_smc_enginepy)
- **Functions (9)**: `clean_symbol()`, `fetch_binance_klines()`, `fetch_binance_funding_rate()`, `detect_liquidity_cluster_hunt()`, `calculate_ema()`, `calculate_atr()`, `detect_ema_momentum_ribbon()`, `detect_funding_rate_squeeze()`, `scan_all_crypto_automation_strategies()`

---

## `crypto_osint_forensics_hub.py`
- **File Path**: [`.agents/tools/crypto_osint_forensics_hub.py`](file:///.agents/tools/crypto_osint_forensics_hub.py)
- **Summary**: Unified Crypto OSINT & Forensics Intelligence Hub Synthesizing: 1. Agent Reach (Social discovery, Reddit sentiment, News RSS, Jina Reader) 2. Flowsint Methodology (Graph-based entity linking, wallet cluster analysis, node/edge export) 3. Akademi Crypto On-Chain Security (Honeypot, Mint/Freeze authority, Liquidity locks)
- **Lines**: 324 | **Size**: 14,013 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`trading_desk.py`](#trading_deskpy)
- **Classes**:
  - `class CryptoOSINTForensicsHub` (Methods: __init__, fetch_reddit_alpha, fetch_institutional_headlines, audit_token_dex, generate_flowsint_graph, run_full_intel_cycle)
- **Functions (1)**: `run_investigation_cli()`

---

## `dashboard_server.py`
- **File Path**: [`.agents/tools/dashboard_server.py`](file:///.agents/tools/dashboard_server.py)
- **Summary**: Web Visual Mission Control HTTP Server & API Bridge Serves dashboard.html, real-time klines with calculated VWAP/Volume Profile, and provides two-way remote control endpoints for Binance Futures.
- **Lines**: 2740 | **Size**: 125,830 bytes
- **Imports (Outbound)**: [`adaptive_ml_engine.py`](#adaptive_ml_enginepy), [`adversarial_debate.py`](#adversarial_debatepy), [`agent_memory_engine.py`](#agent_memory_enginepy), [`ai_risk_officer.py`](#ai_risk_officerpy), [`benchmark_alpha_tracker.py`](#benchmark_alpha_trackerpy), [`binance_client.py`](#binance_clientpy), [`binance_ws_stream.py`](#binance_ws_streampy), [`coinbase_premium.py`](#coinbase_premiumpy), [`coinglass_derivatives.py`](#coinglass_derivativespy), [`crypto_automation_strategies.py`](#crypto_automation_strategiespy), [`crypto_osint_forensics_hub.py`](#crypto_osint_forensics_hubpy), [`dex_futures_bridge.py`](#dex_futures_bridgepy), [`dex_pump_radar.py`](#dex_pump_radarpy), [`dominance_compass.py`](#dominance_compasspy), [`fast_scalper.py`](#fast_scalperpy), [`fomo_smc_engine.py`](#fomo_smc_enginepy), [`fred_macro_intel.py`](#fred_macro_intelpy), [`hedge_fund_seasonality_engine.py`](#hedge_fund_seasonality_enginepy), [`hyperopt_optimizer.py`](#hyperopt_optimizerpy), [`institutional_quant_strategies.py`](#institutional_quant_strategiespy), [`liquidity_heatmap.py`](#liquidity_heatmappy), [`local_cognitive_brain.py`](#local_cognitive_brainpy), [`macro_liquidity.py`](#macro_liquiditypy), [`macro_news_shield.py`](#macro_news_shieldpy), [`market_eyes.py`](#market_eyespy), [`market_radar.py`](#market_radarpy), [`market_regime.py`](#market_regimepy), [`market_structure.py`](#market_structurepy), [`monte_carlo_risk_simulator.py`](#monte_carlo_risk_simulatorpy), [`mt5_client.py`](#mt5_clientpy), [`multi_source_adapter.py`](#multi_source_adapterpy), [`nautilus_risk_engine.py`](#nautilus_risk_enginepy), [`onchain_whale_tracker.py`](#onchain_whale_trackerpy), [`open_quant_pipeline.py`](#open_quant_pipelinepy), [`orb_scalper.py`](#orb_scalperpy), [`orderbook_delta_sniper.py`](#orderbook_delta_sniperpy), [`orderflow_cvd_scalper.py`](#orderflow_cvd_scalperpy), [`pairlist_pipeline.py`](#pairlist_pipelinepy), [`paperclip_orchestrator.py`](#paperclip_orchestratorpy), [`portfolio_beta_hedger.py`](#portfolio_beta_hedgerpy), [`portfolio_guard.py`](#portfolio_guardpy), [`prop_desk_strategies.py`](#prop_desk_strategiespy), [`quant_backtester.py`](#quant_backtesterpy), [`quant_risk_engine.py`](#quant_risk_enginepy), [`regime_adaptive_switcher.py`](#regime_adaptive_switcherpy), [`rejection_block_engine.py`](#rejection_block_enginepy), [`self_improve.py`](#self_improvepy), [`sentiment_narrative_scanner.py`](#sentiment_narrative_scannerpy), [`session_adaptive_strategy.py`](#session_adaptive_strategypy), [`session_filter.py`](#session_filterpy), [`soros_reflexivity_engine.py`](#soros_reflexivity_enginepy), [`telegram_notifier.py`](#telegram_notifierpy), [`timeseries_quant_forecaster.py`](#timeseries_quant_forecasterpy), [`topdown_confluence.py`](#topdown_confluencepy), [`trade_journal.py`](#trade_journalpy), [`trade_manager.py`](#trade_managerpy), [`trading_desk.py`](#trading_deskpy), [`transaction_cost_guard.py`](#transaction_cost_guardpy), [`tri_perspective_risk.py`](#tri_perspective_riskpy), [`tv_screener_adapter.py`](#tv_screener_adapterpy)
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Classes**:
  - `class MissionControlHandler` (Methods: log_message, end_headers, do_OPTIONS, do_GET, do_POST)
  - `class ThreadedTCPServer` (Methods: handle_error)
- **Functions (10)**: `_run_dex_whale_alert_watcher()`, `_run_feed_cache_updater()`, `ensure_feed_updater_running()`, `get_live_watchlist_rs()`, `get_dashboard_feed_data()`, `get_market_intelligence_data()`, `get_journal_data()`, `get_chart_data()`, `kill_stale_port_holder()`, `run_server()`

---

## `dex_futures_bridge.py`
- **File Path**: [`.agents/tools/dex_futures_bridge.py`](file:///.agents/tools/dex_futures_bridge.py)
- **Summary**: dex_futures_bridge.py - Autonomous DEX Momentum to Binance Futures Auto-Bridge & Black Swan Circuit Breaker Synthesized from Akademi Crypto SMC, Momentum Breakouts, and Institutional Risk Engine.
- **Lines**: 432 | **Size**: 18,152 bytes
- **Imports (Outbound)**: [`binance_client.py`](#binance_clientpy), [`portfolio_beta_hedger.py`](#portfolio_beta_hedgerpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`trade_manager.py`](#trade_managerpy)
- **Classes**:
  - `class DexFuturesBridge` (Methods: __init__, _load_state, _save_state, toggle_bridge, get_binance_futures_symbols, normalize_to_futures_symbol, check_black_swan_circuit_breaker, evaluate_and_bridge_token, _execute_futures_order, get_status_payload)
- **Functions (1)**: `get_bridge_engine()`

---

## `dex_pump_radar.py`
- **File Path**: [`.agents/tools/dex_pump_radar.py`](file:///.agents/tools/dex_pump_radar.py)
- **Summary**: dex_pump_radar.py - Institutional DEX & Trending Pump Live Scanner Part of Belajar Kripto Workstation (Phase 1: Zero-Cost API Engine)
- **Lines**: 530 | **Size**: 23,885 bytes
- **Imports (Outbound)**: [`session_filter.py`](#session_filterpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`onchain_whale_tracker.py`](#onchain_whale_trackerpy)
- **Classes**:
  - `class DexPumpRadar` (Methods: __init__, _http_get_json, fetch_dexscreener_boosts, fetch_geckoterminal_trending, fetch_token_pairs_dexscreener, audit_token_security, calculate_alpha_score, scan_all_trending_pumps, run_full_scan)
- **Functions (2)**: `get_dynamic_volatility_thresholds()`, `get_latest_dex_radar_state()`

---

## `dominance_compass.py`
- **File Path**: [`.agents/tools/dominance_compass.py`](file:///.agents/tools/dominance_compass.py)
- **Summary**: BTC Dominance (BTC.D) & USDT Dominance (USDT.D) Compass Engine Synthesized from Akademi Crypto Module 01 (Fundamental & Macro Top-Down Analysis) Decodes real-time capital rotation between Bitcoin, Altcoins, and Tether (Cash) to prevent buying altcoins during BTC vampire rallies or market-wide cashouts.
- **Lines**: 448 | **Size**: 18,045 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`session_filter.py`](#session_filterpy), [`telegram_notifier.py`](#telegram_notifierpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (10)**: `clean_coin()`, `fetch_coingecko_global()`, `fetch_coinpaprika_global()`, `fetch_btc_price_and_change()`, `load_dominance_history()`, `save_dominance_tick()`, `get_dominance_compass()`, `filter_candidate_by_dominance()`, `format_telegram_compass()`, `get_dominance_regime()`

---

## `fast_scalper.py`
- **File Path**: [`.agents/tools/fast_scalper.py`](file:///.agents/tools/fast_scalper.py)
- **Summary**: Fast Scalper Engine (5m / 15m High-Frequency Protocol for Crypto) Focused exclusively on Institutional Liquidity, SMC Traps, and Structural Retests: 1. 5m ICT Rejection Block & 50% Mean Threshold Bounce 2. 5m 4H-Range Breakout & Re-Entry Failure (Failed Auction Scalp) 3. 5m Inverse Fair Value Gap (IFVG) Liquidity Scalp (Role Reversal) 4. 5m 15m-Key-Level Rectangle Break & Retest (Mulham Sniper Strategy) 5. 5m 20-EMA Dynamic Pullback Trap Scalp (Trend-Following Pullback) 6. 5m Session Liquidity Sweep & Micro-FVG (Smart Money Hunt)
- **Lines**: 1561 | **Size**: 65,758 bytes
- **Imports (Outbound)**: [`binance_ws_stream.py`](#binance_ws_streampy), [`htf_macro_lock.py`](#htf_macro_lockpy), [`hyperopt_optimizer.py`](#hyperopt_optimizerpy), [`market_eyes.py`](#market_eyespy), [`market_radar.py`](#market_radarpy), [`mt5_client.py`](#mt5_clientpy), [`orb_scalper.py`](#orb_scalperpy), [`orderflow_cvd_scalper.py`](#orderflow_cvd_scalperpy), [`rejection_block_engine.py`](#rejection_block_enginepy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`telegram_notifier.py`](#telegram_notifierpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (22)**: `load_optimized_scalper_params()`, `get_15m_context()`, `fetch_scalp_candles()`, `fetch_htf_liquidity_anchors()`, `scan_craig_percoco_morning_routine_scalp()`, `scan_5m_liquidity_sweep_fvg()`, `scan_5m_vwap_mean_reversion()`, `scan_5m_volume_surge_breakout()`, `scan_rejection_block_scalp()`, `fetch_4h_range()`, `scan_4h_range_reentry_scalp()`, `detect_candlestick_fvgs()` *(+ 10 more)*

---

## `flight_simulator.py`
- **File Path**: [`.agents/tools/flight_simulator.py`](file:///.agents/tools/flight_simulator.py)
- **Summary**: Quantitative Flight Simulator (Mesin Jam Terbang AI) Simulates hundreds of historical trades across multiple assets (BTC, ETH, SOL, BNB, XRP) in seconds, generates 100+ sample trade histories, and feeds them into the self_improve engine.
- **Lines**: 261 | **Size**: 10,277 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Functions (6)**: `get_default_user()`, `fetch_klines()`, `calculate_ema()`, `simulate_asset_trades()`, `run_flight_simulator()`, `main()`

---

## `fomo_smc_engine.py`
- **File Path**: [`.agents/tools/fomo_smc_engine.py`](file:///.agents/tools/fomo_smc_engine.py)
- **Summary**: FOMO SMC Master Engine (fomo_smc_engine.py) - Complete 14-Course Synthesis Synthesized from all 14 Global Smart Money Concepts (SMC) Courses on Mr FOMO Trading: 1. Phantom Trading (Fractal S/D & CHoCH) 2. Hustle FX (50% Equilibrium Dealing Range) 3. Vertex Investing (50% Mean Threshold MT & Wick-as-Candle) 4. Flipping Markets (Supply-to-Demand S/D Flips) 5. Precision Markets (Expectational Order Flow) 6. PipFactory Academy (Liquidity Sweeps before Mitigation) 7. VVS Academy (Wyckoff Accumulation Spring & Distribution UTAD) 8. FX Simplified (Clean FVG Imbalances) 9. TraqFX (London & NY Killzone Scalping) 10. MENTFX (Decision Point POI Mapping) 11. WWA Bootcamp (Institutional Funding Candle IFC Engulfing) 12. Eye-Opening FX (Asian Range Judas Swing) 13. Fractal Markets (HTF-to-LTF Alignment) 14. Ultimate Supply & Demand (Zone Freshness & Departure Strength)
- **Lines**: 905 | **Size**: 40,127 bytes
- **Imports (Outbound)**: [`agent_memory_engine.py`](#agent_memory_enginepy), [`crypto_automation_strategies.py`](#crypto_automation_strategiespy), [`hedge_fund_seasonality_engine.py`](#hedge_fund_seasonality_enginepy), [`institutional_quant_strategies.py`](#institutional_quant_strategiespy), [`prop_desk_strategies.py`](#prop_desk_strategiespy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`market_eyes.py`](#market_eyespy), [`market_radar.py`](#market_radarpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (10)**: `fetch_candles()`, `calculate_dealing_range_equilibrium()`, `detect_inducement_traps()`, `detect_ifc_institutional_funding_candle()`, `detect_bos_and_choch()`, `detect_vertex_mean_threshold_and_wicks()`, `detect_supply_demand_flips()`, `detect_wyckoff_spring_utad()`, `detect_craig_percoco_rejection_setup()`, `audit_fomo_smc_setup()`

---

## `fred_macro_intel.py`
- **File Path**: [`.agents/tools/fred_macro_intel.py`](file:///.agents/tools/fred_macro_intel.py)
- **Summary**: FRED Macro & Global Liquidity Intelligence Module Inspired by K-Dense Scientific Agent Skills & Akademi Crypto Module 01 (Fundamental Macro). Fetches, caches, and calculates global liquidity regimes: - US 10Y Treasury Yield (Benchmark Risk-Free Rate) - Dollar Index (DXY) Proxy & Regime - Federal Reserve Net Liquidity Proxy (Fed Total Assets - TGA - Reverse Repo) - High-Yield Corporate Credit Spread
- **Lines**: 94 | **Size**: 3,750 bytes
- **Imports (Outbound)**: [`open_quant_pipeline.py`](#open_quant_pipelinepy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`nautilus_risk_engine.py`](#nautilus_risk_enginepy)
- **Functions (1)**: `get_macro_liquidity_regime()`

---

## `hedge_fund_seasonality_engine.py`
- **File Path**: [`.agents/tools/hedge_fund_seasonality_engine.py`](file:///.agents/tools/hedge_fund_seasonality_engine.py)
- **Summary**: hedge_fund_seasonality_engine.py - Institutional Hedge Fund Seasonality & Calendar Anomaly Engine Inspired by Lewis Trumpeter (Quant Hedge Fund Apprentice / IQCapital Masterclass): "THIS Strategy FLIPPED My Trading"
- **Lines**: 462 | **Size**: 19,894 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`fomo_smc_engine.py`](#fomo_smc_enginepy), [`trading_desk.py`](#trading_deskpy)
- **Functions (7)**: `normalize_symbol()`, `get_payday_inflow_signal()`, `get_autumn_short_hedge_signal()`, `get_day_of_week_signal()`, `evaluate_parameter_robustness()`, `calculate_seasonality_confluence()`, `get_dashboard_seasonality_payload()`

---

## `htf_macro_lock.py`
- **File Path**: [`.agents/tools/htf_macro_lock.py`](file:///.agents/tools/htf_macro_lock.py)
- **Summary**: htf_macro_lock.py - High-Timeframe (HTF) Macro Bias Lock & Anti-Counter Trend Guard Synthesized from Akademi Crypto Module 04 (Top-Down Multi-Timeframe Analysis) & Module 01 (Macro Liquidity).
- **Lines**: 237 | **Size**: 10,644 bytes
- **Imports (Outbound)**: [`binance_ws_stream.py`](#binance_ws_streampy), [`market_regime.py`](#market_regimepy)
- **Imported By (Inbound)**: [`fast_scalper.py`](#fast_scalperpy), [`local_cognitive_brain.py`](#local_cognitive_brainpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (3)**: `_get_cached_asset_regime()`, `_get_cached_btc_regimes()`, `audit_htf_macro_bias()`

---

## `hyperopt_optimizer.py`
- **File Path**: [`.agents/tools/hyperopt_optimizer.py`](file:///.agents/tools/hyperopt_optimizer.py)
- **Summary**: Institutional Hyperparameter Optimization Engine (Hyperopt) Multi-Objective Strategy Optimizer for Belajar Kripto Workspace. Features: - Dual Engine: Optuna TPE Sampler with seamless fallback to Native Adaptive Latin Hypercube Search. - Multi-Objective Targets: Sortino, Sharpe, Calmar, ProfitFactor, and Composite Quality Score. - Strategies: FastScalper, TopDownSMC, OrderflowCVD, and ORB Breakout. - Automatic persistence to .agents/data/optimized_params.json for instant trading desk consumption.
- **Lines**: 565 | **Size**: 23,316 bytes
- **Imports (Outbound)**: [`market_eyes.py`](#market_eyespy), [`quant_backtester.py`](#quant_backtesterpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`fast_scalper.py`](#fast_scalperpy)
- **Functions (7)**: `evaluate_fast_scalper_signals()`, `run_parameterized_backtest()`, `optimize_with_optuna()`, `optimize_with_native_search()`, `save_optimization_results()`, `get_optimized_params()`, `run_hyperopt()`

---

## `institutional_quant_strategies.py`
- **File Path**: [`.agents/tools/institutional_quant_strategies.py`](file:///.agents/tools/institutional_quant_strategies.py)
- **Summary**: institutional_quant_strategies.py - Elite Institutional Quant Trading Strategy Suite Synthesized from Order Flow, Volume Profile, and Derivatives Microstructure:
- **Lines**: 471 | **Size**: 20,281 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`fomo_smc_engine.py`](#fomo_smc_enginepy), [`trading_desk.py`](#trading_deskpy)
- **Functions (8)**: `clean_symbol()`, `fetch_binance_klines()`, `detect_naked_poc_gravity_magnet()`, `fetch_binance_oi_history()`, `detect_oi_divergence_exhaustion()`, `calculate_rsi_series()`, `detect_flash_dump_liquidation_dip()`, `scan_all_institutional_strategies()`

---

## `launcher.py`
- **File Path**: [`.agents/tools/launcher.py`](file:///.agents/tools/launcher.py)
- **Summary**: Greend Malik — Autonomous AI Trading Desk Launcher Interactive Python-driven terminal menu with ANSI colors and non-blocking timeout.
- **Lines**: 226 | **Size**: 12,995 bytes
- **Imports (Outbound)**: [`auto_git_sync.py`](#auto_git_syncpy)
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Classes**:
  - `class C`
- **Functions (7)**: `clear_screen()`, `print_banner()`, `ensure_git_sync()`, `ensure_dashboard()`, `print_menu()`, `get_user_choice()`, `main()`

---

## `liquidity_heatmap.py`
- **File Path**: [`.agents/tools/liquidity_heatmap.py`](file:///.agents/tools/liquidity_heatmap.py)
- **Summary**: Liquidity Heatmap & Order Book Depth Imbalance Engine (Magnet Likuidasi) Synthesized from Akademi Crypto Module 02 (Smart Money Concepts — Liquidity Pools & Order Flow)
- **Lines**: 514 | **Size**: 19,755 bytes
- **Imports (Outbound)**: [`binance_client.py`](#binance_clientpy), [`market_structure.py`](#market_structurepy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`session_filter.py`](#session_filterpy), [`telegram_notifier.py`](#telegram_notifierpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (7)**: `clean_coin()`, `fetch_json()`, `fetch_order_book_depth()`, `calculate_depth_imbalance()`, `calculate_liquidity_clusters()`, `get_liquidity_intelligence()`, `format_telegram_liquidity_report()`

---

## `local_cognitive_brain.py`
- **File Path**: [`.agents/tools/local_cognitive_brain.py`](file:///.agents/tools/local_cognitive_brain.py)
- **Summary**: local_cognitive_brain.py - Local Cognitive AI Brain & Consciousness Orchestrator Synthesized for Belajar Kripto Workstation.
- **Lines**: 766 | **Size**: 30,778 bytes
- **Imports (Outbound)**: [`agent_memory_engine.py`](#agent_memory_enginepy), [`binance_ws_stream.py`](#binance_ws_streampy), [`htf_macro_lock.py`](#htf_macro_lockpy), [`trade_journal.py`](#trade_journalpy)
- **Imported By (Inbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy), [`dashboard_server.py`](#dashboard_serverpy), [`trading_desk.py`](#trading_deskpy), [`watchdog_supervisor.py`](#watchdog_supervisorpy)
- **Functions (15)**: `detect_gpu_hardware_profile()`, `get_hardware_ai_profile()`, `test_local_llm_connection()`, `query_local_llm()`, `get_episodic_memory_context()`, `compile_cognitive_perception()`, `_execute_quant_reflex_fallback()`, `_execute_llm_cognitive_review()`, `find_ollama_executable()`, `ensure_local_llm_service()`, `_cognitive_worker_loop()`, `ensure_cognitive_worker()` *(+ 3 more)*

---

## `macro_liquidity.py`
- **File Path**: [`.agents/tools/macro_liquidity.py`](file:///.agents/tools/macro_liquidity.py)
- **Summary**: Global Macro Liquidity & Sentiment Engine (Fincept Terminal Inspired) Fetches real-time macroeconomic indicators without external API keys: 1. US Dollar Index (DXY) - Global Risk-Off Benchmark 2. US 10-Year Treasury Yield (^TNX) - Global Cost of Capital 3. Crypto Fear & Greed Index - Market Sentiment & Psychology 4. Macro Regime Classifier (RISK_ON, RISK_OFF, NEUTRAL)
- **Lines**: 190 | **Size**: 6,984 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy), [`dashboard_server.py`](#dashboard_serverpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (6)**: `fetch_json()`, `fetch_dxy_index()`, `fetch_us10y_yield()`, `fetch_fear_and_greed_index()`, `get_macro_liquidity_summary()`, `main()`

---

## `macro_news_shield.py`
- **File Path**: [`.agents/tools/macro_news_shield.py`](file:///.agents/tools/macro_news_shield.py)
- **Summary**: Economic Calendar & Macro News Shield (High-Impact Volatility Guard) Protects trading capital from brutal slippage, spread widening, and whipsaw stop-outs caused by Tier-1 Macro US Economic Releases (CPI, PPI, NFP, FOMC, GDP, Fed Rate Decisions).
- **Lines**: 261 | **Size**: 10,155 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`nautilus_risk_engine.py`](#nautilus_risk_enginepy), [`telegram_notifier.py`](#telegram_notifierpy), [`trade_manager.py`](#trade_managerpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (5)**: `fetch_economic_calendar()`, `get_parsed_high_impact_events()`, `audit_news_blackout()`, `should_preemptively_protect_positions()`, `format_telegram_news_agenda()`

---

## `market_eyes.py`
- **File Path**: [`.agents/tools/market_eyes.py`](file:///.agents/tools/market_eyes.py)
- **Summary**: Market Eyes (Mata Agent) - Institutional Market Intelligence Engine Fetches real-time price, multi-timeframe candles, technical indicators (RSI, EMA 20/50/200), Fair Value Gaps (FVG), and Perpetual Funding Rates. Resilient multi-exchange data engine: Binance Vision (Primary) -> Binance Futures -> OKX (Fallback).
- **Lines**: 813 | **Size**: 32,679 bytes
- **Imports (Outbound)**: [`adaptive_indicators.py`](#adaptive_indicatorspy), [`binance_ws_stream.py`](#binance_ws_streampy), [`coinglass_derivatives.py`](#coinglass_derivativespy), [`fomo_smc_engine.py`](#fomo_smc_enginepy), [`rejection_block_engine.py`](#rejection_block_enginepy)
- **Imported By (Inbound)**: [`adaptive_ml_engine.py`](#adaptive_ml_enginepy), [`chart_snapshot.py`](#chart_snapshotpy), [`dashboard_server.py`](#dashboard_serverpy), [`fast_scalper.py`](#fast_scalperpy), [`hyperopt_optimizer.py`](#hyperopt_optimizerpy), [`orb_scalper.py`](#orb_scalperpy), [`orderflow_cvd_scalper.py`](#orderflow_cvd_scalperpy), [`pairlist_pipeline.py`](#pairlist_pipelinepy), [`pyramid_runner_engine.py`](#pyramid_runner_enginepy), [`quant_backtester.py`](#quant_backtesterpy), [`telegram_notifier.py`](#telegram_notifierpy), [`topdown_confluence.py`](#topdown_confluencepy), [`trading_desk.py`](#trading_deskpy)
- **Functions (12)**: `fetch_json()`, `fetch_ticker_data()`, `fetch_funding_rate()`, `fetch_candles()`, `calculate_rsi()`, `calculate_ema()`, `detect_three_touch_setup()`, `calculate_vwap_and_bands()`, `calculate_volume_profile()`, `detect_liquidity_sweep_mss()`, `get_market_eyes()`, `main()`

---

## `market_radar.py`
- **File Path**: [`.agents/tools/market_radar.py`](file:///.agents/tools/market_radar.py)
- **Summary**: market_radar.py - Unified Single-Pass Market Analysis & Strategy Intelligence Engine Consolidates SMC Market Structure, Opening Range Breakout (ORB V4.1), ICT Rejection Blocks, Order Flow CVD, DOM Depth Imbalance, and Relative Strength Radar into a single high-speed module.
- **Lines**: 469 | **Size**: 18,777 bytes
- **Imports (Outbound)**: [`coinglass_derivatives.py`](#coinglass_derivativespy), [`fomo_smc_engine.py`](#fomo_smc_enginepy), [`tv_screener_adapter.py`](#tv_screener_adapterpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`fast_scalper.py`](#fast_scalperpy), [`pairlist_pipeline.py`](#pairlist_pipelinepy), [`timeseries_quant_forecaster.py`](#timeseries_quant_forecasterpy)
- **Functions (9)**: `clean_symbol()`, `format_pair()`, `fetch_candles()`, `analyze_smc_structure()`, `analyze_rejection_blocks()`, `analyze_orb_breakout()`, `get_live_watchlist_rs()`, `get_unified_market_scan()`, `get_tradingview_broad_scan()`

---

## `market_regime.py`
- **File Path**: [`.agents/tools/market_regime.py`](file:///.agents/tools/market_regime.py)
- **Summary**: Market Regime Filter & Classifier (Mata Deteksi Rezim Pasar) Uses ADX (Average Directional Index), ATR (Average True Range), and Multi-EMA Alignment to classify market state into Trending, Ranging/Sideways, or Volatility Squeeze. Routes strategies adaptively to prevent false breakouts and sideways chop.
- **Lines**: 331 | **Size**: 13,212 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy), [`dashboard_server.py`](#dashboard_serverpy), [`htf_macro_lock.py`](#htf_macro_lockpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (8)**: `fetch_klines()`, `calculate_adx_and_atr()`, `calculate_ema()`, `detect_market_regime()`, `filter_candidate_by_regime()`, `display_regime_report()`, `scan_multi_asset_regimes()`, `main()`

---

## `market_structure.py`
- **File Path**: [`.agents/tools/market_structure.py`](file:///.agents/tools/market_structure.py)
- **Summary**: SMC Market Structure & Structural Trailing Stop Engine Synthesized from Akademi Crypto Module 02 (Smart Money Concepts & Order Flow Execution) Detects fractal Swing Highs / Swing Lows, Market Structure Shifts (BOS / CHOCH), and computes protected Higher Lows (HL) and Lower Highs (LH) for dynamic structural trailing stops.
- **Lines**: 351 | **Size**: 13,542 bytes
- **Imports (Outbound)**: [`binance_client.py`](#binance_clientpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`liquidity_heatmap.py`](#liquidity_heatmappy), [`rejection_block_engine.py`](#rejection_block_enginepy), [`telegram_notifier.py`](#telegram_notifierpy), [`trade_manager.py`](#trade_managerpy)
- **Functions (7)**: `clean_coin()`, `calculate_atr()`, `get_asset_sweep_buffer()`, `fetch_candles()`, `detect_swing_pivots()`, `get_protected_structural_stop()`, `format_telegram_market_structure()`

---

## `monte_carlo_risk_simulator.py`
- **File Path**: [`.agents/tools/monte_carlo_risk_simulator.py`](file:///.agents/tools/monte_carlo_risk_simulator.py)
- **Summary**: monte_carlo_risk_simulator.py - Monte Carlo Portfolio Resilience & Stress-Test Engine Inspired by QuantX Studio / Institutional Risk Management Protocols.
- **Lines**: 150 | **Size**: 6,213 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy)
- **Functions (2)**: `load_trade_pnls()`, `run_monte_carlo_simulation()`

---

## `mt5_client.py`
- **File Path**: [`.agents/tools/mt5_client.py`](file:///.agents/tools/mt5_client.py)
- **Summary**: MetaTrader 5 (MT5) Execution & Bridge Engine Institutional-Grade Multi-Asset Bridge for Belajar Kripto Trading Desk.
- **Lines**: 544 | **Size**: 18,554 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`fast_scalper.py`](#fast_scalperpy), [`trade_manager.py`](#trade_managerpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (11)**: `ensure_mt5_connected()`, `get_account_summary()`, `resolve_symbol_name()`, `get_live_tick()`, `calculate_lot_size()`, `place_signal_order()`, `get_open_positions()`, `close_position_by_ticket()`, `close_all_positions()`, `modify_position_sl_tp()`, `get_mt5_candles()`

---

## `multi_source_adapter.py`
- **File Path**: [`.agents/tools/multi_source_adapter.py`](file:///.agents/tools/multi_source_adapter.py)
- **Summary**: Multi-Source Market Data Fallback Adapter & Cross-Asset Macro Sentinel Inspired by curated public APIs (public-apis/public-apis): - Primary Source: Binance Public Market Feed (data-api.binance.vision) - Secondary Source 1: CoinPaprika Free Public API (api.coinpaprika.com) - Secondary Source 2: CoinGecko Public API (api.coingecko.com) - Fiat / Forex Benchmark: Frankfurter Open API (api.frankfurter.app)
- **Lines**: 235 | **Size**: 8,340 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy)
- **Functions (7)**: `clean_symbol()`, `fetch_binance_price()`, `fetch_coinpaprika_price()`, `fetch_coingecko_price()`, `fetch_frankfurter_fx()`, `get_consensus_price()`, `get_multi_source_summary()`

---

## `nautilus_risk_engine.py`
- **File Path**: [`.agents/tools/nautilus_risk_engine.py`](file:///.agents/tools/nautilus_risk_engine.py)
- **Summary**: Nautilus-Inspired Pre-Trade Risk Engine & Portfolio Sizing Gate Inspired by NautilusTrader (nautechsystems/nautilus_trader) & Fincept Institutional Terminal.
- **Lines**: 381 | **Size**: 15,444 bytes
- **Imports (Outbound)**: [`adaptive_ml_engine.py`](#adaptive_ml_enginepy), [`agent_memory_engine.py`](#agent_memory_enginepy), [`fred_macro_intel.py`](#fred_macro_intelpy), [`macro_news_shield.py`](#macro_news_shieldpy), [`soros_reflexivity_engine.py`](#soros_reflexivity_enginepy), [`timeseries_quant_forecaster.py`](#timeseries_quant_forecasterpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (5)**: `get_today_date_str()`, `calculate_today_realized_drawdown()`, `estimate_spread_and_slippage()`, `evaluate_pre_trade_risk()`, `validate_pre_trade_order()`

---

## `onchain_whale_tracker.py`
- **File Path**: [`.agents/tools/onchain_whale_tracker.py`](file:///.agents/tools/onchain_whale_tracker.py)
- **Summary**: Institutional On-Chain Whale & Smart Money Flow Tracker Zero-Cost API: DexScreener L2 Trade Streams, GeckoTerminal L-Pools & Public RPCs. Tracks whale wallet activities, massive swap inflows (> $5k-$10k), and smart money accumulation.
- **Lines**: 565 | **Size**: 23,892 bytes
- **Imports (Outbound)**: [`dex_pump_radar.py`](#dex_pump_radarpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`trading_desk.py`](#trading_deskpy)
- **Classes**:
  - `class OnChainWhaleTracker` (Methods: __init__, load_state, add_custom_wallet, discover_top_pnl_whales, get_top_pnl_leaderboard, audit_token_whale_confluence, scan_whale_swaps_on_trending_tokens, run_full_scan, save_state, print_terminal_report)
- **Functions (2)**: `http_get_json()`, `main()`

---

## `open_quant_pipeline.py`
- **File Path**: [`.agents/tools/open_quant_pipeline.py`](file:///.agents/tools/open_quant_pipeline.py)
- **Summary**: Open Quant & Macro Intelligence Pipeline (OpenBB Free Alternative) Zero-API-Key, 100% Free & Institutional-Grade Market Intelligence Engine:
- **Lines**: 309 | **Size**: 10,982 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`fred_macro_intel.py`](#fred_macro_intelpy)
- **Functions (6)**: `_fetch_json()`, `fetch_yahoo_quote()`, `fetch_defillama_tvl()`, `fetch_stablecoin_flow()`, `get_macro_cross_asset_intel()`, `get_unified_quant_pipeline()`

---

## `orb_scalper.py`
- **File Path**: [`.agents/tools/orb_scalper.py`](file:///.agents/tools/orb_scalper.py)
- **Summary**: ========================================================================================   ⚡ 5m/15m OPENING RANGE BREAKOUT (ORB V4.1) SCALPING ENGINE   Captures high-probability session expansion momentum following the initial 15-minute   opening price discovery window of key market sessions:   - 🇬🇧 London Open ORB: 14:00 - 14:15 WIB (07:00 UTC)   - 🇺🇸 New York Open ORB: 19:30 - 19:45 WIB / 20:30 - 20:45 WIB (12:30/13:30 UTC)   - 🌐 Daily UTC 00:00 Open ORB: 07:00 - 07:15 WIB (00:00 UTC)   - 🔄 Rolling 15m Dynamic Range (Inter-session Fallback)      Integrates Order Flow CVD Delta validation and strict Prop Firm Risk Protocols. ========================================================================================
- **Lines**: 342 | **Size**: 13,707 bytes
- **Imports (Outbound)**: [`market_eyes.py`](#market_eyespy), [`orderflow_cvd_scalper.py`](#orderflow_cvd_scalperpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`fast_scalper.py`](#fast_scalperpy)
- **Functions (6)**: `clean_symbol()`, `get_orb_session_state()`, `calculate_opening_range()`, `scan_5m_orb_scalp()`, `mark_orb_traded()`, `get_orb_summary()`

---

## `orderbook_delta_sniper.py`
- **File Path**: [`.agents/tools/orderbook_delta_sniper.py`](file:///.agents/tools/orderbook_delta_sniper.py)
- **Summary**: orderbook_delta_sniper.py - Market Microstructure Order Book Imbalance & CVD Delta Sniping Engine Inspired by High-Frequency Quantitative Desk Microstructure Analytics & Akademi Crypto Module 02.
- **Lines**: 383 | **Size**: 17,711 bytes
- **Imports (Outbound)**: [`binance_ws_stream.py`](#binance_ws_streampy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (4)**: `fetch_orderbook_depth()`, `fetch_recent_agg_trades()`, `analyze_orderbook_and_delta()`, `audit_sniping_entry()`

---

## `orderflow_cvd_scalper.py`
- **File Path**: [`.agents/tools/orderflow_cvd_scalper.py`](file:///.agents/tools/orderflow_cvd_scalper.py)
- **Summary**: ========================================================================================   🌊 ORDER FLOW, CVD DIVERGENCE & DOM FOOTPRINT SCALPING ENGINE   Calculates real-time Taker Delta Volume, Cumulative Volume Delta (CVD) Divergence,   and Depth-of-Market (DOM) Stacked Imbalances for Crypto Micro-Structure Scalping.      Zero-cost, uses direct Binance USDⓈ-M Futures feeds (/fapi/v1/aggTrades & /fapi/v1/depth). ========================================================================================
- **Lines**: 550 | **Size**: 22,287 bytes
- **Imports (Outbound)**: [`market_eyes.py`](#market_eyespy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`fast_scalper.py`](#fast_scalperpy), [`orb_scalper.py`](#orb_scalperpy)
- **Functions (8)**: `clean_symbol()`, `fetch_recent_agg_trades()`, `fetch_l2_depth()`, `calculate_cvd_metrics()`, `detect_cvd_divergence()`, `analyze_dom_stacked_imbalances()`, `scan_5m_orderflow_cvd_scalp()`, `get_orderflow_summary()`

---

## `pairlist_pipeline.py`
- **File Path**: [`.agents/tools/pairlist_pipeline.py`](file:///.agents/tools/pairlist_pipeline.py)
- **Summary**: Chainable Dynamic Pairlist Pipeline & Market Universe Filter Inspired by Freqtrade Dynamic Pairlists & Institutional Quantitative Asset Selection. Features: - 6-Stage Chainable Filter Pipeline:   1. StaticBlacklistFilter (Removes stables, leveraged tokens, delisted/banned coins)   2. VolumePairListFilter (Sorts and filters by 24h Quote Volume in USDT)   3. PricePrecisionFilter (Removes micro-penny assets with severe tick distortion)   4. SpreadAndFrictionFilter (Enforces Bid-Ask spread <= 0.05% / 5 bps)   5. VolatilityFilter (Enforces active ATR & 24h range between 1.2% and 25.0%)   6. SMCConfluenceRanker (Ranks finalists by SMC Trend, FVG presence & RS Score) - Automatic Caching to .agents/data/dynamic_pairlist.json (2-hour TTL). - Direct integration helper for trading desks and high-frequency scalpers.
- **Lines**: 376 | **Size**: 15,219 bytes
- **Imports (Outbound)**: [`market_eyes.py`](#market_eyespy), [`market_radar.py`](#market_radarpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`trading_desk.py`](#trading_deskpy)
- **Classes**:
  - `class PairlistFilter` (Methods: filter)
  - `class StaticBlacklistFilter` (Methods: __init__, filter)
  - `class VolumePairListFilter` (Methods: __init__, filter)
  - `class PricePrecisionFilter` (Methods: __init__, filter)
  - `class SpreadAndFrictionFilter` (Methods: __init__, filter)
  - `class VolatilityFilter` (Methods: __init__, filter)
  - `class SMCConfluenceRankerFilter` (Methods: __init__, filter)
  - `class DynamicPairlistPipeline` (Methods: __init__, execute)
- **Functions (3)**: `fetch_binance_futures_24hr_tickers()`, `get_active_dynamic_pairlist()`, `get_pairlist_telemetry()`

---

## `paperclip_orchestrator.py`
- **File Path**: [`.agents/tools/paperclip_orchestrator.py`](file:///.agents/tools/paperclip_orchestrator.py)
- **Summary**: ========================================================================================   🏢 PAPERCLIP AUTONOMOUS TRADING FIRM CONTROL PLANE   Orchestration Engine: Org Chart, Heartbeat Scheduling, Ticket-Based Task Delegation,   Zero-Cost Quota Guard, and Human Board of Directors Governance.      Inspired by Paperclip AI (https://github.com/paperclipai/paperclip) ========================================================================================
- **Lines**: 715 | **Size**: 28,366 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`telegram_notifier.py`](#telegram_notifierpy), [`trade_manager.py`](#trade_managerpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (18)**: `load_firm_state()`, `save_firm_state()`, `load_tickets()`, `save_tickets()`, `generate_ticket_id()`, `create_ticket()`, `escalate_ticket()`, `board_approve_ticket()`, `board_reject_ticket()`, `evaluate_board_escalation_criteria()`, `register_candidate_setup()`, `close_ticket()` *(+ 6 more)*

---

## `portfolio_beta_hedger.py`
- **File Path**: [`.agents/tools/portfolio_beta_hedger.py`](file:///.agents/tools/portfolio_beta_hedger.py)
- **Summary**: portfolio_beta_hedger.py - Institutional Dynamic Beta-Neutral Portfolio Hedge & Flash-Crash Shield Synthesized from QuantX Studio & Institutional Multi-Asset Risk Desk Protocols.
- **Lines**: 309 | **Size**: 12,591 bytes
- **Imports (Outbound)**: [`binance_client.py`](#binance_clientpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`dex_futures_bridge.py`](#dex_futures_bridgepy), [`trade_manager.py`](#trade_managerpy)
- **Functions (5)**: `fetch_returns_series()`, `calculate_asset_beta()`, `audit_portfolio_beta_exposure()`, `detect_flash_crash_shock()`, `evaluate_and_execute_portfolio_hedge()`

---

## `portfolio_guard.py`
- **File Path**: [`.agents/tools/portfolio_guard.py`](file:///.agents/tools/portfolio_guard.py)
- **Summary**: Portfolio Correlation & Directional Heat Cap Engine (Akademi Crypto Module 03) Guarantees institutional risk budgeting, multi-asset correlation clustering, and directional exposure caps to prevent catastrophic simultaneous drawdowns.
- **Lines**: 167 | **Size**: 7,064 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`telegram_notifier.py`](#telegram_notifierpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (5)**: `clean_coin()`, `audit_portfolio_heat()`, `filter_candidate_by_correlation()`, `get_scaled_risk_pct()`, `format_telegram_portfolio_heat()`

---

## `prop_desk_strategies.py`
- **File Path**: [`.agents/tools/prop_desk_strategies.py`](file:///.agents/tools/prop_desk_strategies.py)
- **Summary**: prop_desk_strategies.py - Institutional Prop-Desk Alpha Strategy Suite Synthesized from Tape Reading, Auction Market Theory, and Statistical Dispersion:
- **Lines**: 370 | **Size**: 16,378 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`fomo_smc_engine.py`](#fomo_smc_enginepy), [`trading_desk.py`](#trading_deskpy)
- **Functions (6)**: `clean_symbol()`, `fetch_binance_klines()`, `detect_sfp_liquidity_sweep()`, `detect_cvd_absorption_iceberg()`, `detect_vwap_volatility_elasticity()`, `scan_all_prop_desk_strategies()`

---

## `pyramid_runner_engine.py`
- **File Path**: [`.agents/tools/pyramid_runner_engine.py`](file:///.agents/tools/pyramid_runner_engine.py)
- **Summary**: pyramid_runner_engine.py - Smart Pyramiding Engine for Risk-Free Runners Synthesized from Akademi Crypto Module 03 (Money Psychology, Sizing, and Pyramiding Winners).
- **Lines**: 170 | **Size**: 8,213 bytes
- **Imports (Outbound)**: [`binance_client.py`](#binance_clientpy), [`market_eyes.py`](#market_eyespy), [`telegram_notifier.py`](#telegram_notifierpy)
- **Imported By (Inbound)**: [`trade_manager.py`](#trade_managerpy)
- **Functions (3)**: `load_trade_metadata()`, `save_trade_metadata()`, `audit_and_execute_pyramiding()`

---

## `quant_backtester.py`
- **File Path**: [`.agents/tools/quant_backtester.py`](file:///.agents/tools/quant_backtester.py)
- **Summary**: Quantitative Historical Backtester & Monte Carlo Simulator Simulates Top-Down Confluence, 4 Championship Strategies, Breakeven (+1R), and Trailing Stops (+2R+). Calculates institutional hedge-fund metrics: Sharpe, Sortino, Profit Factor, MDD, and 1,000-permutation Monte Carlo.
- **Lines**: 834 | **Size**: 36,944 bytes
- **Imports (Outbound)**: [`market_eyes.py`](#market_eyespy)
- **Imported By (Inbound)**: [`adaptive_ml_engine.py`](#adaptive_ml_enginepy), [`dashboard_server.py`](#dashboard_serverpy), [`hyperopt_optimizer.py`](#hyperopt_optimizerpy)
- **Functions (12)**: `fetch_historical_candles()`, `simulate_strategy_signals()`, `simulate_walk_forward_trades()`, `calculate_distribution_moments()`, `normal_cdf()`, `calculate_deflated_sharpe_ratio()`, `calculate_monte_carlo_p_value()`, `run_anti_overfitting_audit()`, `run_backtest()`, `calculate_metrics()`, `run_monte_carlo()`, `print_backtest_report()`

---

## `quant_risk_engine.py`
- **File Path**: [`.agents/tools/quant_risk_engine.py`](file:///.agents/tools/quant_risk_engine.py)
- **Summary**: Institutional Quantitative Risk Engine (QuantLib-Inspired Suite) Inspired by Fincept Terminal & Professional Hedge Fund Risk Desks.
- **Lines**: 335 | **Size**: 12,281 bytes
- **Imports (Outbound)**: [`trade_journal.py`](#trade_journalpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (8)**: `load_closed_trades()`, `calculate_kelly_criterion()`, `run_monte_carlo_simulation()`, `compute_historical_trade_metrics()`, `compute_portfolio_var()`, `get_full_quant_risk_summary()`, `compute_strategy_kelly_metrics()`, `main()`

---

## `regime_adaptive_switcher.py`
- **File Path**: [`.agents/tools/regime_adaptive_switcher.py`](file:///.agents/tools/regime_adaptive_switcher.py)
- **Summary**: regime_adaptive_switcher.py - Institutional Regime-Adaptive Strategy Switcher (Otomasi Bunglon) Synthesized from QuantX Studio & Akademi Crypto Multi-Condition Routing.
- **Lines**: 335 | **Size**: 13,840 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (6)**: `fetch_klines()`, `calculate_choppiness_index()`, `calculate_bollinger_band_width()`, `calculate_adx_and_atr()`, `analyze_regime_state()`, `get_adaptive_strategy_parameters()`

---

## `rejection_block_engine.py`
- **File Path**: [`.agents/tools/rejection_block_engine.py`](file:///.agents/tools/rejection_block_engine.py)
- **Summary**: ICT Rejection Block Engine (Smart Money Reversal Predictor) Synthesized from Smart Money Concepts (ICT) & Akademi Crypto Advanced Order Flow.
- **Lines**: 354 | **Size**: 15,263 bytes
- **Imports (Outbound)**: [`market_structure.py`](#market_structurepy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`fast_scalper.py`](#fast_scalperpy), [`market_eyes.py`](#market_eyespy), [`telegram_notifier.py`](#telegram_notifierpy)
- **Functions (4)**: `normalize_candles()`, `detect_rejection_blocks()`, `evaluate_retest_status()`, `get_rejection_block_intelligence()`

---

## `scan_tokocrypto.py`
- **File Path**: [`.agents/tools/scan_tokocrypto.py`](file:///.agents/tools/scan_tokocrypto.py)
- **Summary**: No module docstring.
- **Lines**: 99 | **Size**: 3,626 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Functions (2)**: `analyze_coin()`, `run_scan()`

---

## `scan_usdt_pairs.py`
- **File Path**: [`.agents/tools/scan_usdt_pairs.py`](file:///.agents/tools/scan_usdt_pairs.py)
- **Summary**: No module docstring.
- **Lines**: 77 | **Size**: 2,837 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Functions (1)**: `run_scan()`

---

## `self_improve.py`
- **File Path**: [`.agents/tools/self_improve.py`](file:///.agents/tools/self_improve.py)
- **Summary**: Self-Improving AI Trading Engine (The Reflection Brain & Karpathy Autoresearch Loop) Inspired by: 1. ATLAS by General Intelligence Capital (chrisworsey55/atlas-gic) - Karpathy-style Autoresearch Keep-or-Revert 2. Lewis Jackson's "How To Build A Self-Improving AI Trading Agent" 3. Akademi Crypto Quantitative Genome & Risk Architecture.
- **Lines**: 493 | **Size**: 22,669 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`telegram_notifier.py`](#telegram_notifierpy), [`trade_manager.py`](#trade_managerpy)
- **Functions (13)**: `load_json()`, `save_json()`, `get_default_genome()`, `get_all_trade_records()`, `calculate_rolling_sharpe()`, `analyze_performance()`, `run_karpathy_autoresearch_cycle()`, `get_autoresearch_summary()`, `record_closed_trade_and_check_evolution()`, `format_telegram_genome_status()`, `show_genome_status()`, `inject_sample_data()` *(+ 1 more)*

---

## `sentiment_narrative_scanner.py`
- **File Path**: [`.agents/tools/sentiment_narrative_scanner.py`](file:///.agents/tools/sentiment_narrative_scanner.py)
- **Summary**: Sentiment & Social Narrative Scanner Inspired by Tauric Research's TradingAgents Analyst Architecture (arXiv:2412.20138) and Akademi Crypto Module 01 (Macro Sentiment, Capital Rotation & Narrative Trading).
- **Lines**: 442 | **Size**: 18,031 bytes
- **Imports (Outbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy)
- **Imported By (Inbound)**: [`adversarial_debate.py`](#adversarial_debatepy), [`ai_risk_officer.py`](#ai_risk_officerpy), [`dashboard_server.py`](#dashboard_serverpy), [`telegram_notifier.py`](#telegram_notifierpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (7)**: `fetch_json()`, `get_fear_and_greed_index()`, `get_narrative_sector_rotation()`, `get_social_virality_trending()`, `classify_catalyst_sentiment()`, `get_market_sentiment_narrative_summary()`, `get_token_narrative_info()`

---

## `session_adaptive_strategy.py`
- **File Path**: [`.agents/tools/session_adaptive_strategy.py`](file:///.agents/tools/session_adaptive_strategy.py)
- **Summary**: session_adaptive_strategy.py - 24/7 Session-Adaptive Multi-Regime Strategy Engine Dynamically aligns algorithmic trading strategies with the 4 distinct global liquidity sessions:
- **Lines**: 203 | **Size**: 8,533 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`trade_manager.py`](#trade_managerpy)
- **Functions (3)**: `get_active_24h_regime()`, `calculate_asian_range_and_judas_setup()`, `audit_trade_dormancy_and_stall()`

---

## `session_filter.py`
- **File Path**: [`.agents/tools/session_filter.py`](file:///.agents/tools/session_filter.py)
- **Summary**: Institutional Trading Sessions & Kill Zones Filter + Confluence Scoring Engine Synthesized with Akademi Crypto (Smart Money Concepts & Order Flow Execution).
- **Lines**: 572 | **Size**: 25,985 bytes
- **Imports (Outbound)**: [`coinbase_premium.py`](#coinbase_premiumpy), [`dominance_compass.py`](#dominance_compasspy), [`liquidity_heatmap.py`](#liquidity_heatmappy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`dex_pump_radar.py`](#dex_pump_radarpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (6)**: `get_current_session_info()`, `is_scalping_killzone_active()`, `classify_strategy_archetype()`, `get_adaptive_threshold()`, `calculate_confluence_score()`, `audit_candidate_confluence()`

---

## `smart_money_tracker.py`
- **File Path**: [`.agents/tools/smart_money_tracker.py`](file:///.agents/tools/smart_money_tracker.py)
- **Summary**: Smart Money & On-Chain Copy-Trade Auditor (Pelacak Whale & Copy-Trade Institusional) Synthesized from DaviddTech FOMO Copy-Trading Strategy & Akademi Crypto Module 02 & 06. Audits whale wallet consistency, follower crowding risk, token liquidity, and safe position sizing.
- **Lines**: 336 | **Size**: 14,877 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Functions (5)**: `audit_whale_metrics()`, `audit_binance_lead_trader()`, `audit_dex_token()`, `calculate_copy_sizing()`, `main()`

---

## `soros_reflexivity_engine.py`
- **File Path**: [`.agents/tools/soros_reflexivity_engine.py`](file:///.agents/tools/soros_reflexivity_engine.py)
- **Summary**: Soros Reflexivity Feedback Engine Inspired by George Soros's Theory of Reflexivity and ATLAS GIC (General Intelligence Capital).
- **Lines**: 178 | **Size**: 7,330 bytes
- **Imports (Outbound)**: [`coinglass_derivatives.py`](#coinglass_derivativespy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`nautilus_risk_engine.py`](#nautilus_risk_enginepy)
- **Functions (2)**: `get_soros_reflexivity_index()`, `evaluate_pre_trade_reflexivity()`

---

## `telegram_notifier.py`
- **File Path**: [`.agents/tools/telegram_notifier.py`](file:///.agents/tools/telegram_notifier.py)
- **Summary**: Telegram Real-Time Alert & Two-Way Remote Control Notifier Bridges Autonomous Binance Trading Desk with Telegram Bot API. Provides instant trade notifications, PnL summaries, and remote command listener.
- **Lines**: 1977 | **Size**: 99,965 bytes
- **Imports (Outbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy), [`binance_client.py`](#binance_clientpy), [`chart_snapshot.py`](#chart_snapshotpy), [`coinbase_premium.py`](#coinbase_premiumpy), [`coinglass_derivatives.py`](#coinglass_derivativespy), [`dominance_compass.py`](#dominance_compasspy), [`fast_scalper.py`](#fast_scalperpy), [`liquidity_heatmap.py`](#liquidity_heatmappy), [`macro_news_shield.py`](#macro_news_shieldpy), [`market_eyes.py`](#market_eyespy), [`market_structure.py`](#market_structurepy), [`paperclip_orchestrator.py`](#paperclip_orchestratorpy), [`portfolio_guard.py`](#portfolio_guardpy), [`rejection_block_engine.py`](#rejection_block_enginepy), [`self_improve.py`](#self_improvepy), [`sentiment_narrative_scanner.py`](#sentiment_narrative_scannerpy), [`trade_journal.py`](#trade_journalpy), [`trade_manager.py`](#trade_managerpy), [`trading_desk.py`](#trading_deskpy)
- **Imported By (Inbound)**: [`binance_client.py`](#binance_clientpy), [`chart_snapshot.py`](#chart_snapshotpy), [`dashboard_server.py`](#dashboard_serverpy), [`pyramid_runner_engine.py`](#pyramid_runner_enginepy), [`trade_manager.py`](#trade_managerpy), [`trading_desk.py`](#trading_deskpy), [`watchdog_supervisor.py`](#watchdog_supervisorpy)
- **Classes**:
  - `class TelegramCommandListener` (Methods: __init__, run, _fetch_updates, run, _fetch_updates, _handle_callback, _handle_command)
- **Functions (31)**: `_check_and_register_dedup()`, `_save_dedup_response()`, `parse_env_file()`, `get_telegram_config()`, `load_desk_state()`, `save_desk_state()`, `is_desk_paused()`, `get_desk_mode()`, `setup_bot_commands()`, `send_telegram_msg()`, `notify_trade_opened()`, `notify_ai_officer_veto()` *(+ 19 more)*

---

## `timeseries_quant_forecaster.py`
- **File Path**: [`.agents/tools/timeseries_quant_forecaster.py`](file:///.agents/tools/timeseries_quant_forecaster.py)
- **Summary**: Quantitative Time-Series & Volatility Forecaster Module Inspired by K-Dense Scientific Agent Skills (TimesFM / scikit-learn / scientific quant methods). Calculates: - Realized EWMA Volatility & Parkinson High-Low Volatility - Value-at-Risk (VaR 95% & VaR 99%) (Parametric & Historical Simulation) - Expected Shortfall / Conditional VaR (CVaR) - Dynamic SL Volatility Buffer Recommendation
- **Lines**: 165 | **Size**: 5,298 bytes
- **Imports (Outbound)**: [`market_radar.py`](#market_radarpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`nautilus_risk_engine.py`](#nautilus_risk_enginepy)
- **Functions (2)**: `calculate_parkinson_volatility()`, `get_asset_volatility_profile()`

---

## `tokocrypto_client.py`
- **File Path**: [`.agents/tools/tokocrypto_client.py`](file:///.agents/tools/tokocrypto_client.py)
- **Summary**: Tokocrypto Spot Trading Client (Multi-Account Enabled) Supports isolated API credentials per user email (e.g. dxmade@gmail.com). Regulated by Bappebti / OJK Indonesia.
- **Lines**: 303 | **Size**: 12,977 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Functions (12)**: `sanitize_email_suffix()`, `parse_env_file()`, `get_all_configured_users()`, `resolve_credentials()`, `get_exchange()`, `check_balance()`, `get_ticker()`, `get_open_orders()`, `place_order()`, `cancel_order()`, `list_users()`, `main()`

---

## `topdown_confluence.py`
- **File Path**: [`.agents/tools/topdown_confluence.py`](file:///.agents/tools/topdown_confluence.py)
- **Summary**: Multi-Timeframe Confluence Engine (Top-Down Macro Analysis) Harmonizes Higher Timeframe (4H / 1D) Macro Bias with Lower Timeframe (15m / 1H) Sniper Executions. Strictly filters out counter-trend trades and fakeouts to trade in confluence with Smart Money.
- **Lines**: 217 | **Size**: 8,459 bytes
- **Imports (Outbound)**: [`market_eyes.py`](#market_eyespy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (2)**: `analyze_macro_structure()`, `check_topdown_alignment()`

---

## `trade_hands.py`
- **File Path**: [`.agents/tools/trade_hands.py`](file:///.agents/tools/trade_hands.py)
- **Summary**: Trade Hands (Tangan Agent) - Institutional Paper Trading & Order Execution Engine Supports Multi-Account Portfolio Isolation per User Email.
- **Lines**: 430 | **Size**: 18,547 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Functions (12)**: `get_default_user()`, `get_portfolio_path()`, `get_live_price()`, `load_portfolio()`, `save_portfolio()`, `open_position()`, `update_positions()`, `close_position_manual()`, `show_history()`, `show_status()`, `reset_portfolio()`, `main()`

---

## `trade_journal.py`
- **File Path**: [`.agents/tools/trade_journal.py`](file:///.agents/tools/trade_journal.py)
- **Summary**: Automated Trade Journal & Performance Analytics Engine Synthesized from Akademi Crypto Module 03 (Money Psychology & Trading Plan) Tracks complete trade lifecycles, aggregates execution metrics from Binance Futures, and computes institutional quant metrics (Win Rate, Profit Factor, Expectancy, Payoff Ratio, Max Drawdown).
- **Lines**: 725 | **Size**: 31,175 bytes
- **Imports (Outbound)**: [`agent_memory_engine.py`](#agent_memory_enginepy), [`atomic_json_store.py`](#atomic_json_storepy), [`auto_git_sync.py`](#auto_git_syncpy), [`binance_client.py`](#binance_clientpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`local_cognitive_brain.py`](#local_cognitive_brainpy), [`quant_risk_engine.py`](#quant_risk_enginepy), [`telegram_notifier.py`](#telegram_notifierpy), [`trade_manager.py`](#trade_managerpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (14)**: `load_journal()`, `load_archived_trades()`, `load_all_trades()`, `load_trade_ledger()`, `load_bot_executions()`, `archive_older_trades()`, `save_journal()`, `normalize_strategy_name()`, `normalize_existing_journal_strategies()`, `record_closed_trade()`, `sync_binance_history()`, `calculate_journal_metrics()` *(+ 2 more)*

---

## `trade_manager.py`
- **File Path**: [`.agents/tools/trade_manager.py`](file:///.agents/tools/trade_manager.py)
- **Summary**: Dynamic Trade Management Engine (CEO Risk & Position Protection) Handles Breakeven Auto-Lock (+1R) and Chandelier / R-Multiple Trailing Stops (+2R+). Guarantees institutional risk-free positions and profit locking across 24/7 cycles.
- **Lines**: 1416 | **Size**: 72,698 bytes
- **Imports (Outbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy), [`atomic_json_store.py`](#atomic_json_storepy), [`binance_client.py`](#binance_clientpy), [`binance_ws_stream.py`](#binance_ws_streampy), [`dex_futures_bridge.py`](#dex_futures_bridgepy), [`macro_news_shield.py`](#macro_news_shieldpy), [`market_structure.py`](#market_structurepy), [`mt5_client.py`](#mt5_clientpy), [`paperclip_orchestrator.py`](#paperclip_orchestratorpy), [`portfolio_beta_hedger.py`](#portfolio_beta_hedgerpy), [`pyramid_runner_engine.py`](#pyramid_runner_enginepy), [`self_improve.py`](#self_improvepy), [`session_adaptive_strategy.py`](#session_adaptive_strategypy), [`telegram_notifier.py`](#telegram_notifierpy), [`trade_journal.py`](#trade_journalpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`telegram_notifier.py`](#telegram_notifierpy), [`trading_desk.py`](#trading_deskpy)
- **Classes**:
  - `class FastPositionWatcher` (Methods: __init__, run, stop)
- **Functions (11)**: `load_trade_metadata()`, `save_trade_metadata()`, `record_trade_entry()`, `format_qty_precision()`, `calculate_breakeven_price()`, `update_binance_stop_loss()`, `execute_manual_partial_tp()`, `fetch_closed_trade_details()`, `audit_and_manage_positions()`, `audit_and_manage_mt5_positions()`, `start_fast_watcher()`

---

## `trading_desk.py`
- **File Path**: [`.agents/tools/trading_desk.py`](file:///.agents/tools/trading_desk.py)
- **Summary**: Autonomous Multi-Agent Trading Desk (CEO Orchestrator) Inspired by DaviddTech / Lewis Jackson Multi-Agent AI Trading Desk. Synthesized with Akademi Crypto SMC (Smart Money Concepts), FVG, and Strict Risk Rules.
- **Lines**: 2232 | **Size**: 115,720 bytes
- **Imports (Outbound)**: [`adaptive_indicators.py`](#adaptive_indicatorspy), [`ai_risk_officer.py`](#ai_risk_officerpy), [`auto_git_sync.py`](#auto_git_syncpy), [`binance_client.py`](#binance_clientpy), [`binance_ws_stream.py`](#binance_ws_streampy), [`coinbase_premium.py`](#coinbase_premiumpy), [`coinglass_derivatives.py`](#coinglass_derivativespy), [`crypto_osint_forensics_hub.py`](#crypto_osint_forensics_hubpy), [`dominance_compass.py`](#dominance_compasspy), [`fast_scalper.py`](#fast_scalperpy), [`fomo_smc_engine.py`](#fomo_smc_enginepy), [`hedge_fund_seasonality_engine.py`](#hedge_fund_seasonality_enginepy), [`htf_macro_lock.py`](#htf_macro_lockpy), [`institutional_quant_strategies.py`](#institutional_quant_strategiespy), [`liquidity_heatmap.py`](#liquidity_heatmappy), [`local_cognitive_brain.py`](#local_cognitive_brainpy), [`macro_liquidity.py`](#macro_liquiditypy), [`macro_news_shield.py`](#macro_news_shieldpy), [`market_eyes.py`](#market_eyespy), [`market_regime.py`](#market_regimepy), [`mt5_client.py`](#mt5_clientpy), [`nautilus_risk_engine.py`](#nautilus_risk_enginepy), [`onchain_whale_tracker.py`](#onchain_whale_trackerpy), [`orderbook_delta_sniper.py`](#orderbook_delta_sniperpy), [`pairlist_pipeline.py`](#pairlist_pipelinepy), [`paperclip_orchestrator.py`](#paperclip_orchestratorpy), [`portfolio_guard.py`](#portfolio_guardpy), [`prop_desk_strategies.py`](#prop_desk_strategiespy), [`quant_risk_engine.py`](#quant_risk_enginepy), [`regime_adaptive_switcher.py`](#regime_adaptive_switcherpy), [`sentiment_narrative_scanner.py`](#sentiment_narrative_scannerpy), [`session_filter.py`](#session_filterpy), [`telegram_notifier.py`](#telegram_notifierpy), [`topdown_confluence.py`](#topdown_confluencepy), [`trade_journal.py`](#trade_journalpy), [`trade_manager.py`](#trade_managerpy), [`transaction_cost_guard.py`](#transaction_cost_guardpy)
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`telegram_notifier.py`](#telegram_notifierpy)
- **Classes**:
  - `class C`
- **Functions (21)**: `get_effective_watchlist()`, `acquire_single_instance_lock()`, `ensure_dashboard_daemon()`, `load_genome()`, `get_asset_sweep_buffer()`, `get_dynamic_futures_watchlist()`, `get_adaptive_kelly_risk_pct()`, `log_desk_activity()`, `export_dashboard_feed()`, `get_active_positions()`, `get_account_financials()`, `get_account_balance()` *(+ 9 more)*

---

## `transaction_cost_guard.py`
- **File Path**: [`.agents/tools/transaction_cost_guard.py`](file:///.agents/tools/transaction_cost_guard.py)
- **Summary**: transaction_cost_guard.py - Transaction Cost & Slippage Memory Engine Inspired by Open-Finance-Lab/AgenticTrading (transaction_cost_agent_pool & storage).
- **Lines**: 293 | **Size**: 12,852 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`trading_desk.py`](#trading_deskpy)
- **Functions (6)**: `load_memory()`, `save_memory()`, `record_fill_telemetry()`, `audit_pre_trade_transaction_drag()`, `evaluate_net_profit_hurdle()`, `get_transaction_cost_summary()`

---

## `tri_perspective_risk.py`
- **File Path**: [`.agents/tools/tri_perspective_risk.py`](file:///.agents/tools/tri_perspective_risk.py)
- **Summary**: Tri-Perspective Risk Balancing Layer (Aggressive, Neutral, Conservative) Inspired by Tauric Research's TradingAgents Multi-Agent Framework (arXiv:2412.20138) Adapted for 24/7 Autonomous Crypto Trading & Quantitative Risk Governance.
- **Lines**: 390 | **Size**: 16,603 bytes
- **Imports (Outbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy)
- **Imported By (Inbound)**: [`ai_risk_officer.py`](#ai_risk_officerpy), [`dashboard_server.py`](#dashboard_serverpy)
- **Functions (5)**: `load_tri_risk_history()`, `save_tri_risk_record()`, `run_deterministic_tri_risk()`, `run_llm_tri_risk()`, `run_tri_perspective_risk()`

---

## `tv_screener_adapter.py`
- **File Path**: [`.agents/tools/tv_screener_adapter.py`](file:///.agents/tools/tv_screener_adapter.py)
- **Summary**: TradingView Screener Institutional Adapter (tvscreener) Broad-market scanner, multi-timeframe technical indicator harvester, and DEX/CEX momentum discovery. Synthesized with Akademi Crypto Top-Down Screening & Institutional Confluence Framework.
- **Lines**: 329 | **Size**: 13,234 bytes
- **Imports (Outbound)**: *None (Leaf Module)*
- **Imported By (Inbound)**: [`dashboard_server.py`](#dashboard_serverpy), [`market_radar.py`](#market_radarpy)
- **Functions (6)**: `clean_base_symbol()`, `format_technical_rating()`, `scan_binance_futures_universe()`, `get_tradingview_technical_summary()`, `scan_dex_and_altcoin_gems()`, `_fallback_binance_scan()`

---

## `watchdog_supervisor.py`
- **File Path**: [`.agents/tools/watchdog_supervisor.py`](file:///.agents/tools/watchdog_supervisor.py)
- **Summary**: Auto-Healing Watchdog Supervisor Daemon Supervises Mission Control Dashboard Server and Autonomous Trading Desk. Detects unexpected terminations, unhandled exceptions, or port collisions, and automatically revives processes with exponential backoff and Telegram alerts.
- **Lines**: 291 | **Size**: 10,597 bytes
- **Imports (Outbound)**: [`local_cognitive_brain.py`](#local_cognitive_brainpy), [`telegram_notifier.py`](#telegram_notifierpy)
- **Imported By (Inbound)**: *Top-Level / Entry Script*
- **Classes**:
  - `class ServiceWatcher` (Methods: __init__, is_alive, check_http_health, kill_stale_port, start, restart, tick)
- **Functions (1)**: `run_supervisor()`

---

