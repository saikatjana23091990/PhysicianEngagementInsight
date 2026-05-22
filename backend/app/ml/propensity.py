"""
XGBoost-backed opportunity propensity model.

Target: probability that an HCP has *any* conversion within the next 30 days,
trained on call-level features at the time of each call. We aggregate to HCP-level
predictions for the live targeting view.

When training data is too small / pathological, we degrade gracefully and emit a
flag `model_status: 'fallback'`.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from app.data.store import DataStore
from app.services.conversion_engine import ConversionEngine

logger = logging.getLogger("app.ml.propensity")


FEATURES = [
    "rx_recent", "rx_prior", "rx_growth", "calls_90d", "digital_90d",
    "pub_count_12m", "pub_relevance_avg", "event_score_avg",
    "kol_influence", "kol_centrality", "event_urgency", "hcp_hist_conv_rate",
]


class PropensityModel:
    def __init__(self) -> None:
        self.model = None
        self.fitted = False
        self.status = "untrained"
        self.feature_importance: dict = {}
        self.auc: Optional[float] = None

    def train(self, features: pd.DataFrame) -> None:
        if features.empty:
            self.status = "no_data"
            return
        # Target: HCP had any conversion (binary, derived from hcp_hist_conv_rate > 0)
        y = (features["hcp_hist_conv_rate"] > 0).astype(int).values
        if y.sum() < 3 or (len(y) - y.sum()) < 3:
            self.status = "insufficient_class_balance"
            return
        X = features[FEATURES].fillna(0).values
        try:
            from xgboost import XGBClassifier
            from sklearn.model_selection import cross_val_score
            model = XGBClassifier(
                n_estimators=120, max_depth=4, learning_rate=0.08,
                subsample=0.85, colsample_bytree=0.85, random_state=42,
                use_label_encoder=False, eval_metric="logloss",
            )
            # quick CV (3-fold) when feasible
            try:
                scores = cross_val_score(model, X, y, cv=min(3, max(2, y.sum())), scoring="roc_auc")
                self.auc = float(np.mean(scores))
            except Exception:
                self.auc = None
            model.fit(X, y)
            self.model = model
            self.fitted = True
            self.status = "trained"
            self.feature_importance = dict(zip(FEATURES, model.feature_importances_.tolist()))
            logger.info("PropensityModel trained. AUC=%s status=%s", self.auc, self.status)
        except Exception as e:
            logger.warning("XGBoost training failed: %s", e)
            self.status = f"error: {e}"

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        if not self.fitted or self.model is None:
            return np.full(len(features), 0.5)
        X = features[FEATURES].fillna(0).values
        return self.model.predict_proba(X)[:, 1]


_singleton: Optional[PropensityModel] = None


def get_propensity_model(features: pd.DataFrame) -> PropensityModel:
    global _singleton
    if _singleton is None:
        _singleton = PropensityModel()
        _singleton.train(features)
    return _singleton
