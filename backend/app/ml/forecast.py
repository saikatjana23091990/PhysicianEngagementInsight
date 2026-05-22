"""
Forecasting: Holt-Winters (statsmodels) with EWM fallback.
Returns N forecast points with confidence intervals.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("app.ml.forecast")


def forecast_holt_winters(series: pd.Series, steps: int = 8) -> pd.DataFrame:
    """series is a weekly numeric series indexed by date. Returns DataFrame with
    columns: forecast, low, high."""
    if len(series) < 6:
        return _ewm_fallback(series, steps)
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        model = ExponentialSmoothing(
            series.astype(float).values,
            trend="add",
            seasonal=None,
            initialization_method="estimated",
        )
        fit = model.fit(optimized=True)
        fc = fit.forecast(steps)
        resid_std = float(np.nanstd(series.values - fit.fittedvalues)) or 2.5
        out = pd.DataFrame({
            "forecast": np.maximum(0.0, fc).round(2),
            "low": np.maximum(0.0, fc - 1.96 * resid_std).round(2),
            "high": (fc + 1.96 * resid_std).round(2),
        })
        return out
    except Exception as e:
        logger.warning("Holt-Winters failed: %s. Falling back to EWM.", e)
        return _ewm_fallback(series, steps)


def _ewm_fallback(series: pd.Series, steps: int) -> pd.DataFrame:
    vals = series.astype(float).values
    if len(vals) == 0:
        return pd.DataFrame(columns=["forecast", "low", "high"])
    level = float(vals[0])
    alpha = 0.4
    for v in vals[1:]:
        level = alpha * v + (1 - alpha) * level
    trend = float(np.mean(np.diff(vals[-4:]))) if len(vals) >= 4 else 0.0
    fc = np.array([max(0.0, level + trend * i) for i in range(1, steps + 1)])
    return pd.DataFrame({
        "forecast": fc.round(2),
        "low": np.maximum(0.0, fc - 2.5).round(2),
        "high": (fc + 2.5).round(2),
    })
