import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from typing import Dict, Any, List, Tuple, Optional
from app.features.extractor import extract_signal_features

MODULATION_CLASSES = ["BPSK", "QPSK", "8PSK", "2FSK", "4FSK", "16QAM", "64QAM", "AM", "FM"]

class ModulationClassifierEngine:
    """
    Multi-Modal Modulation Classifier supporting IQ-Only, WAV-Only, and Fused IQ+WAV modes.
    """
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.iq_model_path = os.path.join(model_dir, "iq_classifier.joblib")
        self.wav_model_path = os.path.join(model_dir, "wav_classifier.joblib")
        self.fused_model_path = os.path.join(model_dir, "fused_classifier.joblib")

        self.iq_model: Optional[HistGradientBoostingClassifier] = None
        self.wav_model: Optional[HistGradientBoostingClassifier] = None
        self.fused_model: Optional[HistGradientBoostingClassifier] = None

        self.classes = MODULATION_CLASSES
        self.is_trained = False
        self._load_or_train_baseline()

    def _load_or_train_baseline(self):
        if (os.path.exists(self.iq_model_path) and 
            os.path.exists(self.wav_model_path) and 
            os.path.exists(self.fused_model_path)):
            try:
                self.iq_model = joblib.load(self.iq_model_path)
                self.wav_model = joblib.load(self.wav_model_path)
                self.fused_model = joblib.load(self.fused_model_path)
                self.is_trained = True
                return
            except Exception:
                pass

        # Train baseline models on synthetic signals
        self.train_baseline_models()

    def train_baseline_models(self, n_samples_per_class: int = 40):
        """
        Trains IQ-only, WAV-only, and Fused classifiers using synthetic signal generation.
        """
        from app.ml.generator import generate_synthetic_rf_signal

        x_iq, x_wav, x_fused, y_labels = [], [], [], []

        for mod in self.classes:
            for snr in [8.0, 12.0, 16.0, 22.0]:
                for _ in range(n_samples_per_class // 4):
                    # Generate IQ signal
                    iq_sig, _ = generate_synthetic_rf_signal(modulation=mod, snr_db=snr)
                    iq_feat, _ = extract_signal_features(iq_sig, 1000000.0)

                    # Simulate WAV audio signal / channel representation with slight perturbation
                    wav_noise = (np.random.normal(0, 0.05, len(iq_sig)) + 
                                 1j * np.random.normal(0, 0.05, len(iq_sig))).astype(np.complex64)
                    wav_sig = iq_sig + wav_noise
                    wav_feat, _ = extract_signal_features(wav_sig, 1000000.0)

                    fused_feat = np.concatenate([iq_feat, wav_feat])

                    x_iq.append(iq_feat)
                    x_wav.append(wav_feat)
                    x_fused.append(fused_feat)
                    y_labels.append(mod)

        x_iq = np.array(x_iq)
        x_wav = np.array(x_wav)
        x_fused = np.array(x_fused)
        y_labels = np.array(y_labels)

        self.iq_model = HistGradientBoostingClassifier(max_iter=100, random_state=42)
        self.iq_model.fit(x_iq, y_labels)

        self.wav_model = HistGradientBoostingClassifier(max_iter=100, random_state=42)
        self.wav_model.fit(x_wav, y_labels)

        self.fused_model = HistGradientBoostingClassifier(max_iter=100, random_state=42)
        self.fused_model.fit(x_fused, y_labels)

        joblib.dump(self.iq_model, self.iq_model_path)
        joblib.dump(self.wav_model, self.wav_model_path)
        joblib.dump(self.fused_model, self.fused_model_path)
        self.is_trained = True

    def classify_signal(
        self,
        iq_signal: Optional[np.ndarray],
        wav_signal: Optional[np.ndarray],
        sample_rate: float,
        conservative_confidence: bool = False,
    ) -> Dict[str, Any]:
        """
        Runs ML classification based on available inputs.
        If both IQ and WAV are available -> Fused mode + side-by-side mode comparisons!
        """
        if not self.is_trained:
            self._load_or_train_baseline()

        iq_feat = None
        wav_feat = None
        mode = "IQ Only"

        if iq_signal is not None:
            iq_feat, _ = extract_signal_features(iq_signal, sample_rate)

        if wav_signal is not None:
            wav_feat, _ = extract_signal_features(wav_signal, sample_rate)

        if iq_signal is not None and wav_signal is not None:
            mode = "Paired IQ + WAV Fusion"
        elif iq_signal is not None:
            mode = "IQ Only"
        else:
            mode = "WAV Only"

        # Predictions per model
        iq_preds = self._predict_single_model(self.iq_model, iq_feat, conservative_confidence) if iq_feat is not None else None
        wav_preds = self._predict_single_model(self.wav_model, wav_feat, conservative_confidence) if wav_feat is not None else None
        
        fused_preds = None
        if iq_feat is not None and wav_feat is not None:
            fused_vec = np.concatenate([iq_feat, wav_feat])
            fused_preds = self._predict_single_model(self.fused_model, fused_vec, conservative_confidence)

        # Primary prediction decision
        if mode == "Paired IQ + WAV Fusion" and fused_preds is not None:
            primary = fused_preds
        elif iq_preds is not None:
            primary = iq_preds
        else:
            primary = wav_preds

        return {
            "mode": mode,
            "prediction": primary["top_prediction"],
            "confidence": primary["confidence_pct"],
            "raw_confidence": primary["raw_confidence_pct"],
            "confidence_method": primary["confidence_method"],
            "candidates": primary["top_candidates"],
            "mode_comparisons": {
                "iq_only": iq_preds["top_prediction"] + f" ({iq_preds['confidence_pct']}%)" if iq_preds else "N/A",
                "wav_only": wav_preds["top_prediction"] + f" ({wav_preds['confidence_pct']}%)" if wav_preds else "N/A",
                "fused": fused_preds["top_prediction"] + f" ({fused_preds['confidence_pct']}%)" if fused_preds else "N/A"
            }
        }

    def _predict_single_model(self, model: HistGradientBoostingClassifier, feat: np.ndarray, conservative: bool) -> Dict[str, Any]:
        probs = model.predict_proba([feat])[0]
        class_order = model.classes_
        raw_top_confidence = float(np.max(probs)) * 100.0

        # These models are trained only on synthetic signals.  Temperature
        # scaling makes their output deliberately conservative for an
        # unannotated recording rather than claiming synthetic-test certainty.
        if conservative:
            probs = np.power(np.clip(probs, 1e-12, 1.0), 1.0 / 3.0)
            probs = probs / np.sum(probs)
            # Reserve probability mass for distribution shift: these baseline
            # models have not been calibrated on this real recording domain.
            probs = 0.70 * probs + (0.30 / len(probs))
        
        # Sort top candidates
        top_idx = np.argsort(probs)[::-1]
        top_candidates = []
        for idx in top_idx[:3]:
            top_candidates.append({
                "modulation": str(class_order[idx]),
                "confidence_pct": round(float(probs[idx]) * 100.0, 1)
            })

        return {
            "top_prediction": top_candidates[0]["modulation"],
            "confidence_pct": top_candidates[0]["confidence_pct"],
            "raw_confidence_pct": round(raw_top_confidence, 1),
            "confidence_method": "Conservative temperature-scaled probability" if conservative else "Model probability",
            "top_candidates": top_candidates
        }
