"""
Modelo Supervisado — Random Forest con Etiqueta Sintética
Implementa la sección 9 del reto: 'Machine Learning supervisado —
Predicción de probabilidad de posible fraude usando etiqueta simulada.'

La etiqueta se genera a partir del score de reglas (≥76 → fraude posible)
dado que el dataset no incluye etiqueta_fraude_simulada explícita.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    roc_auc_score, roc_curve, confusion_matrix,
    precision_score, recall_score, f1_score,
)
from sklearn.preprocessing import StandardScaler

from src.anomaly_model import build_feature_matrix, FEATURE_LABELS


def train_random_forest(sheets: dict, scores_df: pd.DataFrame) -> dict:
    """
    Entrena Random Forest con etiqueta sintética generada del score de reglas.
    Retorna métricas, scores por siniestro, importancia de variables y curva ROC.
    """
    feat, meta = build_feature_matrix(sheets)
    if feat.empty or scores_df.empty:
        return {}

    # Alinear con scores
    merged = meta.merge(
        scores_df[["ID Siniestro", "Score", "Nivel"]],
        on="ID Siniestro", how="left",
    )
    X = feat.values.astype(float)

    # Escalar
    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X)

    # Generar etiqueta inteligente e independiente para evitar circularidad (data leakage)
    # Entrenamos un Isolation Forest interno rápido para evaluar atipicidades estadísticas
    from sklearn.ensemble import IsolationForest
    iso = IsolationForest(contamination=0.25, random_state=42)
    iso_scores = iso.fit(X_sc).decision_function(X_sc)
    is_min, is_max = iso_scores.min(), iso_scores.max()
    iso_norm_scores = ((is_max - iso_scores) / (is_max - is_min) * 100)

    # Combinamos anomalía numérica >= 60 con presencia de discrepancias en PDFs (N_Alertas > 0 o reglas críticas)
    n_alerts = merged.merge(scores_df[["ID Siniestro", "N_Alertas", "Reglas Críticas"]], on="ID Siniestro", how="left")
    n_alerts["N_Alertas"] = n_alerts["N_Alertas"].fillna(0)
    n_alerts["Tiene_Critica"] = n_alerts["Reglas Críticas"].fillna("").apply(lambda val: len(str(val)) > 0)

    y = ((iso_norm_scores >= 60) & ((n_alerts["N_Alertas"] >= 1) | n_alerts["Tiene_Critica"])).astype(int).values

    # Modelo
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    # Cross-validation estratificada 5-fold
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_auc = cross_val_score(rf, X_sc, y, cv=cv, scoring="roc_auc", n_jobs=-1)
    cv_f1  = cross_val_score(rf, X_sc, y, cv=cv, scoring="f1",      n_jobs=-1)
    cv_pre = cross_val_score(rf, X_sc, y, cv=cv, scoring="precision",n_jobs=-1)
    cv_rec = cross_val_score(rf, X_sc, y, cv=cv, scoring="recall",   n_jobs=-1)

    # Fit final
    rf.fit(X_sc, y)
    y_pred = rf.predict(X_sc)
    y_prob = rf.predict_proba(X_sc)[:, 1]

    # Curva ROC
    fpr, tpr, _ = roc_curve(y, y_prob)
    auc_score   = roc_auc_score(y, y_prob)

    # Confusion matrix
    cm = confusion_matrix(y, y_pred)

    # Feature importance (ordenada)
    fi_raw  = rf.feature_importances_
    fi_dict = {
        FEATURE_LABELS.get(col, col): float(fi_raw[i])
        for i, col in enumerate(feat.columns)
    }
    fi_dict = dict(sorted(fi_dict.items(), key=lambda x: -x[1]))

    # Scores por siniestro (0–100)
    rf_scores = (y_prob * 100).round(1)
    result_df = meta.copy()
    result_df["RF_Score"]      = rf_scores
    result_df["RF_Prediction"] = y_pred
    result_df["RF_Label"]      = y

    return {
        "model":   rf,
        "scaler":  scaler,
        "scores_df": result_df,
        "metrics": {
            "auc":          round(float(auc_score),     4),
            "cv_auc_mean":  round(float(cv_auc.mean()),  4),
            "cv_auc_std":   round(float(cv_auc.std()),   4),
            "cv_f1_mean":   round(float(cv_f1.mean()),   4),
            "cv_f1_std":    round(float(cv_f1.std()),    4),
            "cv_pre_mean":  round(float(cv_pre.mean()),  4),
            "cv_rec_mean":  round(float(cv_rec.mean()),  4),
            "precision":    round(float(precision_score(y, y_pred, zero_division=0)), 4),
            "recall":       round(float(recall_score(y, y_pred,    zero_division=0)), 4),
            "f1":           round(float(f1_score(y, y_pred,        zero_division=0)), 4),
            "confusion_matrix": cm.tolist(),
            "n_positivos":  int(y.sum()),
            "n_total":      len(y),
        },
        "feature_importance": fi_dict,
        "roc_fpr":   fpr.tolist(),
        "roc_tpr":   tpr.tolist(),
        "feature_names": list(feat.columns),
    }


def combined_score(
    rule_score: float,
    if_score:   float,
    rf_score:   float,
    w_rules: float = 0.50,
    w_if:    float = 0.25,
    w_rf:    float = 0.25,
) -> tuple[int, str]:
    """
    Score Final Combinado = 50% Reglas + 25% Isolation Forest + 25% Random Forest.
    Preserva piso de ROJO si las reglas críticas (RF-01..RF-04) clasifican como ROJO.
    """
    combined = round(w_rules * rule_score + w_if * if_score + w_rf * rf_score)
    combined = max(0, min(100, combined))

    # Si las reglas críticas marcaron ROJO (rule_score>=76), preservar mínimo
    if rule_score >= 76:
        combined = max(combined, 76)

    nivel = "ROJO" if combined >= 76 else "AMARILLO" if combined >= 41 else "VERDE"
    return combined, nivel


def build_combined_df(
    scores_df: pd.DataFrame,
    if_result: dict,
    rf_result: dict,
) -> pd.DataFrame:
    """Fusiona los tres scores en un DataFrame único."""
    df = scores_df[["ID Siniestro","Ramo","Cobertura","Sucursal",
                    "Score","Nivel","Alertas","Monto Reclamado"]].copy()
    df.rename(columns={"Score": "Score_Reglas", "Nivel": "Nivel_Reglas"}, inplace=True)

    if if_result and "scores_df" in if_result:
        if_df = if_result["scores_df"][["ID Siniestro","Anomaly_Score"]].copy()
        df = df.merge(if_df, on="ID Siniestro", how="left")
        df["Anomaly_Score"] = df["Anomaly_Score"].fillna(50)
    else:
        df["Anomaly_Score"] = 50

    if rf_result and "scores_df" in rf_result:
        rf_df = rf_result["scores_df"][["ID Siniestro","RF_Score"]].copy()
        df = df.merge(rf_df, on="ID Siniestro", how="left")
        df["RF_Score"] = df["RF_Score"].fillna(50)
    else:
        df["RF_Score"] = 50

    results = df.apply(
        lambda r: combined_score(r["Score_Reglas"], r["Anomaly_Score"], r["RF_Score"]),
        axis=1,
    )
    df["Score_Final"] = [r[0] for r in results]
    df["Nivel_Final"] = [r[1] for r in results]
    color_map = {"ROJO": "#E74C3C", "AMARILLO": "#F39C12", "VERDE": "#27AE60"}
    df["Color_Final"] = df["Nivel_Final"].map(color_map)

    return df.sort_values("Score_Final", ascending=False).reset_index(drop=True)
