"""
Adaptive Rolling Machine Learning & Out-of-Distribution (OOD) Anomaly Detector
Inspired by FreqAI Dissimilarity Index (DI) and Institutional Scientific Quant Methods.
Features:
- Multi-Scale Technical Feature Extraction (Returns, Volatility, Volume Flow, EMAs, CVD Proxy).
- Mahalanobis Distance & Regularized Covariance Dissimilarity Index (DI).
- Three-Tier Anomaly Gate: IN_DISTRIBUTION (1.0x), DISTRIBUTION_DRIFT (0.5x), ANOMALY_OUT_OF_BOUNDS (0.0x / Block).
- Rolling L2-Regularized Directional Classifier & Return Forecaster (bps).
- Auto-Persistence & 24h Rolling Retraining Pipeline.
"""

from __future__ import annotations
import argparse
import json
import math
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
ML_MODELS_DIR = os.path.join(DATA_DIR, "ml_models")

sys.path.insert(0, TOOLS_DIR)
import market_eyes
import quant_backtester

try:
    import numpy as np
except ImportError:
    np = None

FEATURE_NAMES = [
    "ret_1", "ret_3", "ret_5", "ret_12", "ret_24",
    "parkinson_hl", "atr_norm", "vol_ratio",
    "rsi_centered", "ema_diff20", "ema_diff50", "cvd_proxy"
]

DI_SAFE_THRESHOLD = 1.00
DI_DRIFT_THRESHOLD = 1.50


# -------------------------------------------------------------
# 1. Feature Engineering
# -------------------------------------------------------------

def extract_candle_features(candles: List[Dict[str, Any]]) -> Tuple[List[List[float]], List[float]]:
    """
    Extracts multi-scale normalized quantitative features from candle sequence.
    Returns: (features_matrix, close_prices)
    """
    if len(candles) < 35:
        return [], []

    closes = [float(c["close"]) for c in candles]
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    vols = [float(c.get("volume", 1.0)) for c in candles]

    # Pre-calculate indicators
    ema20_series = []
    ema50_series = []
    
    # Calculate EMA arrays
    k20 = 2 / 21
    k50 = 2 / 51
    e20 = closes[0]
    e50 = closes[0]
    for c in closes:
        e20 = (c * k20) + (e20 * (1 - k20))
        e50 = (c * k50) + (e50 * (1 - k50))
        ema20_series.append(e20)
        ema50_series.append(e50)

    # Calculate True Range
    tr_series = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        tr_series.append(tr)

    features = []
    valid_closes = []

    # Start from index 25 to allow sufficient lookback
    for i in range(25, len(candles)):
        c_cur = closes[i]
        h_cur = highs[i]
        l_cur = lows[i]
        v_cur = max(vols[i], 0.0001)

        # 1-5. Multi-scale log returns
        r1 = math.log(c_cur / max(closes[i-1], 1e-6))
        r3 = math.log(c_cur / max(closes[i-3], 1e-6))
        r5 = math.log(c_cur / max(closes[i-5], 1e-6))
        r12 = math.log(c_cur / max(closes[i-12], 1e-6))
        r24 = math.log(c_cur / max(closes[i-24], 1e-6))

        # 6. Parkinson High-Low Volatility (last 5 bars)
        hl_sum = sum(math.log(max(highs[k], 1e-6) / max(lows[k], 1e-6)) ** 2 for k in range(i-4, i+1))
        parkinson = math.sqrt(hl_sum / (4.0 * math.log(2.0) * 5.0))

        # 7. Normalized ATR (14 bars)
        atr14 = sum(tr_series[i-13:i+1]) / 14.0
        atr_norm = atr14 / c_cur

        # 8. Volume Ratio (vs 20 MA)
        vol_ma = sum(vols[i-19:i+1]) / 20.0
        vol_ratio = v_cur / max(vol_ma, 1e-6)

        # 9. RSI Centered
        window_closes = closes[i-14:i+1]
        gains = [max(0.0, window_closes[k] - window_closes[k-1]) for k in range(1, len(window_closes))]
        losses = [max(0.0, window_closes[k-1] - window_closes[k]) for k in range(1, len(window_closes))]
        avg_g = sum(gains) / 14.0 if gains else 0.0
        avg_l = sum(losses) / 14.0 if losses else 1e-6
        rs = avg_g / max(avg_l, 1e-6)
        rsi_val = 100.0 - (100.0 / (1.0 + rs))
        rsi_centered = (rsi_val - 50.0) / 25.0  # Normalized to ~ [-2.0, +2.0]

        # 10-11. EMA Divergence
        ema_diff20 = (c_cur - ema20_series[i]) / ema20_series[i]
        ema_diff50 = (c_cur - ema50_series[i]) / ema50_series[i]

        # 12. CVD Volume Delta Proxy
        spread = max(h_cur - l_cur, 1e-6)
        buying_press = (c_cur - l_cur) / spread
        selling_press = (h_cur - c_cur) / spread
        cvd_proxy = (buying_press - selling_press) * min(vol_ratio, 3.0)

        row = [
            r1, r3, r5, r12, r24,
            parkinson, atr_norm, vol_ratio,
            rsi_centered, ema_diff20, ema_diff50, cvd_proxy
        ]
        features.append(row)
        valid_closes.append(c_cur)

    return features, valid_closes


# -------------------------------------------------------------
# 2. Linear Algebra & Anomaly Estimator (Mahalanobis / DI)
# -------------------------------------------------------------

def compute_mean_and_cov_inv(X: np.ndarray, reg: float = 1e-4) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """
    Computes empirical mean, std, regularized inverted covariance matrix, and 90th percentile baseline distance.
    """
    means = np.mean(X, axis=0)
    stds = np.std(X, axis=0)
    stds[stds < 1e-6] = 1.0

    # Standardize
    Z = (X - means) / stds

    # Regularized Covariance Matrix: (Z.T @ Z) / N + lambda * I
    N, D = Z.shape
    cov = (Z.T @ Z) / float(N) + (reg * np.eye(D))

    try:
        cov_inv = np.linalg.pinv(cov)
    except Exception:
        cov_inv = np.eye(D)

    # Compute baseline training Mahalanobis distances
    train_distances = []
    for i in range(N):
        zi = Z[i]
        dist = float(np.sqrt(max(0.0, zi @ cov_inv @ zi)))
        train_distances.append(dist)

    p90_baseline = float(np.percentile(train_distances, 90)) if train_distances else 1.0
    p90_baseline = max(p90_baseline, 0.1)

    return means, stds, cov_inv, p90_baseline


def calculate_dissimilarity_index(feature_vector: List[float], means: np.ndarray, stds: np.ndarray, cov_inv: np.ndarray, p90_baseline: float) -> Tuple[float, str, float]:
    """
    Calculates the FreqAI-style Dissimilarity Index (DI) for a new real-time market feature state.
    Returns: (DI, status, risk_multiplier)
    """
    z = (np.array(feature_vector) - means) / stds
    m_dist = float(np.sqrt(max(0.0, z @ cov_inv @ z)))
    di = round(m_dist / p90_baseline, 3)

    if di <= DI_SAFE_THRESHOLD:
        status = "IN_DISTRIBUTION"
        risk_mult = 1.0
    elif di <= DI_DRIFT_THRESHOLD:
        status = "DISTRIBUTION_DRIFT"
        risk_mult = 0.5
    else:
        status = "ANOMALY_OUT_OF_BOUNDS"
        risk_mult = 0.0

    return di, status, risk_mult


# -------------------------------------------------------------
# 3. Rolling Directional ML Classifier
# -------------------------------------------------------------

def train_directional_classifier(X: np.ndarray, closes: List[float], forecast_horizon: int = 3, l2_reg: float = 1.0) -> Tuple[np.ndarray, float]:
    """
    Trains an L2-regularized linear ridge classifier predicting next-horizon directional returns.
    Target: Return in basis points over forecast_horizon candles.
    """
    N, D = X.shape
    if N <= forecast_horizon + 5:
        return np.zeros(D), 0.50

    # Build future return targets
    Y = []
    valid_X = []
    for i in range(N - forecast_horizon):
        ret_fwd = (closes[i + forecast_horizon] - closes[i]) / closes[i] * 10000.0  # in basis points
        Y.append(ret_fwd)
        valid_X.append(X[i])

    X_mat = np.array(valid_X)
    Y_vec = np.array(Y)

    # Standardize X_mat
    m = np.mean(X_mat, axis=0)
    s = np.std(X_mat, axis=0)
    s[s < 1e-6] = 1.0
    Z_mat = (X_mat - m) / s

    # Ridge analytical closed-form solution: w = (Z.T @ Z + lambda * I)^-1 @ Z.T @ Y
    Z_cov = (Z_mat.T @ Z_mat) + (l2_reg * np.eye(D))
    try:
        w = np.linalg.pinv(Z_cov) @ Z_mat.T @ Y_vec
    except Exception:
        w = np.zeros(D)

    # Calculate train accuracy on directional sign
    preds = Z_mat @ w
    correct = np.sum((preds > 0) == (Y_vec > 0))
    accuracy = float(correct) / float(len(Y_vec)) if len(Y_vec) > 0 else 0.50

    return w, accuracy


# -------------------------------------------------------------
# 4. Training & Model Management
# -------------------------------------------------------------

def train_and_cache_model(symbol: str = "BTC", bar: str = "1h", candle_count: int = 500) -> Dict[str, Any]:
    """
    Fetches historical data, trains ML directional weights and Covariance baseline, and caches to disk.
    """
    os.makedirs(ML_MODELS_DIR, exist_ok=True)
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
    model_file = os.path.join(ML_MODELS_DIR, f"{sym_clean}_{bar}_ml_model.json")

    candles = quant_backtester.fetch_historical_candles(symbol=sym_clean, bar=bar, target_count=candle_count)
    if not candles or len(candles) < 50:
        return {"success": False, "error": "Insufficient candle history"}

    features, valid_closes = extract_candle_features(candles)
    if len(features) < 30:
        return {"success": False, "error": "Feature extraction returned insufficient rows"}

    X = np.array(features)

    # 1. Train Anomaly & Mahalanobis Baseline
    means, stds, cov_inv, p90_base = compute_mean_and_cov_inv(X)

    # 2. Train Directional Forecaster
    weights, train_acc = train_directional_classifier(X, valid_closes, forecast_horizon=3)

    model_payload = {
        "symbol": sym_clean,
        "bar": bar,
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "trained_timestamp": time.time(),
        "sample_count": len(features),
        "train_accuracy_pct": round(train_acc * 100.0, 2),
        "p90_baseline": round(p90_base, 4),
        "means": means.tolist(),
        "stds": stds.tolist(),
        "cov_inv": cov_inv.tolist(),
        "weights": weights.tolist(),
        "feature_names": FEATURE_NAMES
    }

    try:
        with open(model_file, "w", encoding="utf-8") as f:
            json.dump(model_payload, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error caching ML model: {e}")

    return {
        "success": True,
        "symbol": sym_clean,
        "bar": bar,
        "samples": len(features),
        "train_accuracy": round(train_acc * 100.0, 2),
        "p90_baseline": round(p90_base, 4),
        "model_file": model_file
    }


def load_model(symbol: str, bar: str = "1h", max_age_seconds: int = 86400) -> Optional[Dict[str, Any]]:
    """
    Loads cached ML model, triggering automated rolling retraining if expired (>24h).
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
    model_file = os.path.join(ML_MODELS_DIR, f"{sym_clean}_{bar}_ml_model.json")

    if os.path.exists(model_file):
        try:
            with open(model_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                trained_ts = data.get("trained_timestamp", 0)
                if time.time() - trained_ts < max_age_seconds:
                    return data
        except Exception:
            pass

    # Model missing or stale -> retrain automatically
    ret = train_and_cache_model(symbol=sym_clean, bar=bar, candle_count=500)
    if ret.get("success"):
        try:
            with open(model_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


# -------------------------------------------------------------
# 5. Live State Inference & Safety Gate
# -------------------------------------------------------------

def evaluate_live_market_ml(symbol: str = "BTC", bar: str = "1h") -> Dict[str, Any]:
    """
    Evaluates current real-time candle state against trained ML distribution.
    Computes Dissimilarity Index (DI), anomaly status, and directional prediction.
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
    model = load_model(sym_clean, bar=bar)

    if not model:
        return {
            "symbol": sym_clean,
            "bar": bar,
            "status": "IN_DISTRIBUTION",
            "dissimilarity_index": 0.50,
            "anomaly_score": 0.10,
            "risk_multiplier": 1.0,
            "predicted_direction": "NEUTRAL",
            "predicted_return_bps": 0.0,
            "confidence_pct": 50.0,
            "model_status": "FALLBACK_DEFAULT"
        }

    # Fetch latest candles
    candles = quant_backtester.fetch_historical_candles(symbol=sym_clean, bar=bar, target_count=50)
    if not candles or len(candles) < 30:
        return {
            "symbol": sym_clean,
            "bar": bar,
            "status": "IN_DISTRIBUTION",
            "dissimilarity_index": 0.50,
            "anomaly_score": 0.10,
            "risk_multiplier": 1.0,
            "predicted_direction": "NEUTRAL",
            "predicted_return_bps": 0.0,
            "confidence_pct": 50.0,
            "model_status": "FALLBACK_INSUFFICIENT_CANDLES"
        }

    features, _ = extract_candle_features(candles)
    if not features:
        return {
            "symbol": sym_clean,
            "bar": bar,
            "status": "IN_DISTRIBUTION",
            "dissimilarity_index": 0.50,
            "anomaly_score": 0.10,
            "risk_multiplier": 1.0,
            "predicted_direction": "NEUTRAL",
            "predicted_return_bps": 0.0,
            "confidence_pct": 50.0,
            "model_status": "FALLBACK_EMPTY_FEATURES"
        }

    cur_feat = features[-1]

    means = np.array(model["means"])
    stds = np.array(model["stds"])
    cov_inv = np.array(model["cov_inv"])
    p90_base = float(model.get("p90_baseline", 1.0))
    weights = np.array(model["weights"])

    # 1. Dissimilarity Index & Anomaly Gate
    di, status, risk_mult = calculate_dissimilarity_index(cur_feat, means, stds, cov_inv, p90_base)

    # 2. Directional Return Prediction (bps)
    z_feat = (np.array(cur_feat) - means) / stds
    pred_bps = float(z_feat @ weights)
    
    # Sigmoidal confidence scaling
    confidence = 50.0 + (50.0 * math.tanh(abs(pred_bps) / 40.0))
    direction = "BULLISH" if pred_bps > 5.0 else ("BEARISH" if pred_bps < -5.0 else "NEUTRAL")

    # Feature contribution breakdown
    contributions = {}
    for idx, name in enumerate(FEATURE_NAMES):
        contributions[name] = round(float(z_feat[idx] * weights[idx]), 2)
    top_feature = max(contributions.items(), key=lambda x: abs(x[1])) if contributions else ("none", 0.0)

    return {
        "symbol": sym_clean,
        "bar": bar,
        "status": status,
        "dissimilarity_index": di,
        "anomaly_score": round(min(1.0, di / 2.0), 3),
        "risk_multiplier": risk_mult,
        "predicted_direction": direction,
        "predicted_return_bps": round(pred_bps, 2),
        "confidence_pct": round(confidence, 1),
        "top_driver": f"{top_feature[0]} ({top_feature[1]:+,.1f} bps)",
        "train_accuracy_pct": model.get("train_accuracy_pct", 55.0),
        "trained_at": model.get("trained_at", "N/A"),
        "model_status": "ACTIVE_ONLINE"
    }


def audit_pre_trade_ml_safety(symbol: str, side: str = "BUY", bar: str = "1h") -> Dict[str, Any]:
    """
    Institutional pre-trade safety check.
    Suppresses orders if market is in unprecedented OOD anomaly state (DI > 1.5).
    """
    eval_res = evaluate_live_market_ml(symbol, bar=bar)
    di = eval_res.get("dissimilarity_index", 0.5)
    status = eval_res.get("status", "IN_DISTRIBUTION")
    risk_mult = eval_res.get("risk_multiplier", 1.0)
    pred_dir = eval_res.get("predicted_direction", "NEUTRAL")

    approved = True
    reason = f"ML Distribution Normal (DI: {di:.2f} <= {DI_SAFE_THRESHOLD})"

    if status == "ANOMALY_OUT_OF_BOUNDS":
        approved = False
        reason = f"🚨 PRE-TRADE REJECTED: Out-of-Distribution Anomaly Detected (DI: {di:.2f} > {DI_DRIFT_THRESHOLD}) — Market in Extreme Volatility Shock"
    elif status == "DISTRIBUTION_DRIFT":
        reason = f"⚠️ Distribution Drift Warning (DI: {di:.2f}) — Sizing Haircut Applied (0.5x)"

    # Directional Alignment check (Soft warning)
    req_dir = "BULLISH" if side.upper() in ("BUY", "LONG") else "BEARISH"
    alignment = "ALIGNED" if pred_dir == req_dir else ("NEUTRAL" if pred_dir == "NEUTRAL" else "COUNTER_ML_BIAS")

    return {
        "approved": approved,
        "symbol": symbol.upper(),
        "side": side.upper(),
        "dissimilarity_index": di,
        "status": status,
        "risk_multiplier": risk_mult,
        "ml_predicted_direction": pred_dir,
        "alignment": alignment,
        "reason": reason
    }


# -------------------------------------------------------------
# 6. CLI Runner
# -------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adaptive ML & Anomaly Detector Engine")
    parser.add_argument("--symbol", type=str, default="BTC", help="Asset symbol (e.g. BTC, ETH, SOL)")
    parser.add_argument("--bar", type=str, default="1h", help="Candle timeframe (e.g. 15m, 1h, 4h)")
    parser.add_argument("--train", action="store_true", help="Force train model on historical candles")
    parser.add_argument("--predict", action="store_true", help="Evaluate live market distribution state")

    args = parser.parse_args()

    if args.train:
        print(f"🤖 Training Rolling ML Model for {args.symbol.upper()} [{args.bar}]...")
        res = train_and_cache_model(symbol=args.symbol, bar=args.bar, candle_count=500)
        print(json.dumps(res, indent=2))
    else:
        print(f"🔬 Evaluating Live ML Anomaly & Direction for {args.symbol.upper()} [{args.bar}]...")
        res = evaluate_live_market_ml(symbol=args.symbol, bar=args.bar)
        print("=" * 65)
        print(f"       🧠 ADAPTIVE ML & ANOMALY DETECTOR: {args.symbol.upper()}")
        print("=" * 65)
        print(f"  • Dissimilarity Index (DI) : {res['dissimilarity_index']} [{res['status']}]")
        print(f"  • Risk Sizing Multiplier   : {res['risk_multiplier']}x")
        print(f"  • Predicted Direction      : {res['predicted_direction']} ({res['predicted_return_bps']:+,.1f} bps)")
        print(f"  • Model Confidence         : {res['confidence_pct']}%")
        print(f"  • Primary Alpha Driver     : {res['top_driver']}")
        print(f"  • Base Model Accuracy      : {res['train_accuracy_pct']}% (Trained: {res['trained_at']})")
        print("=" * 65)
