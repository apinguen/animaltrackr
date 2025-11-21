"""Lightweight TensorFlow Lite inference helpers for Pi Zero builds."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np

try:  # pragma: no cover - optional dependency
    import tflite_runtime.interpreter as tflite  # type: ignore
except (ImportError, RuntimeError):
    try:  # pragma: no cover - fallback
        from tensorflow import lite as tflite  # type: ignore
    except (ImportError, RuntimeError):
        tflite = None  # type: ignore


@dataclass(slots=True)
class Prediction:
    """Single inference result."""

    label: str
    score: float
    bbox: Tuple[float, float, float, float] | None = None


class InferenceEngine:
    """Wrap a TFLite interpreter with simple preprocessing/postprocessing."""

    def __init__(
        self,
        model_path: str | Path,
        labels: Sequence[str] | None = None,
        threshold: float = 0.5,
    ) -> None:
        self.model_path = Path(model_path)
        self.labels = list(labels) if labels else []
        self.threshold = threshold
        self._interpreter = None
        self._input_details = None
        self._output_details = None
        self._model_ready = False
        self._load_model()

    # ------------------------------------------------------------------
    def _load_model(self) -> None:
        if tflite is None:
            logging.warning("tflite-runtime not installed; inference disabled")
            return

        if not self.model_path.exists():
            logging.warning("Model %s not found; inference disabled", self.model_path)
            return

        interpreter = tflite.Interpreter(model_path=str(self.model_path))
        interpreter.allocate_tensors()
        self._interpreter = interpreter
        self._input_details = interpreter.get_input_details()[0]
        self._output_details = interpreter.get_output_details()
        self._model_ready = True
        logging.info("Loaded TFLite model from %s", self.model_path)

    # ------------------------------------------------------------------
    def predict(self, frame: np.ndarray) -> List[Prediction]:
        """Run inference on a single RGB frame."""

        if not self._model_ready or self._interpreter is None or self._input_details is None:
            logging.debug("Skipping inference; interpreter not ready")
            return []

        input_tensor = self._preprocess(frame)
        self._interpreter.set_tensor(self._input_details["index"], input_tensor)
        self._interpreter.invoke()

        if not self._output_details:
            return []

        return self._postprocess()

    def close(self) -> None:
        """Release interpreter resources."""

        self._interpreter = None
        self._input_details = None
        self._output_details = None
        self._model_ready = False

    # ------------------------------------------------------------------
    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        details = self._input_details
        if details is None:
            raise RuntimeError("Interpreter not initialised")

        target_height, target_width = details["shape"][1:3]
        resized = np.resize(frame, (target_height, target_width, 3))
        tensor = np.expand_dims(resized, axis=0)
        return tensor.astype(np.float32)

    def _postprocess(self) -> List[Prediction]:
        assert self._output_details is not None and self._interpreter is not None
        predictions: List[Prediction] = []

        outputs = [self._interpreter.get_tensor(detail["index"]) for detail in self._output_details]
        if len(outputs) == 1:
            scores = outputs[0].flatten()
            for idx, score in enumerate(scores):
                if score < self.threshold:
                    continue
                label = self.labels[idx] if idx < len(self.labels) else f"class_{idx}"
                predictions.append(Prediction(label=label, score=float(score)))
            return predictions

        # Treat multi-output models as SSD-style detectors when shapes match
        boxes, classes, scores = outputs[:3]
        for box, cls, score in zip(boxes[0], classes[0], scores[0]):
            if score < self.threshold:
                continue
            label_idx = int(cls)
            label = self.labels[label_idx] if label_idx < len(self.labels) else f"class_{label_idx}"
            y_min, x_min, y_max, x_max = box.tolist()
            predictions.append(
                Prediction(
                    label=label,
                    score=float(score),
                    bbox=(x_min, y_min, x_max, y_max),
                )
            )
        return predictions


__all__ = ["InferenceEngine", "Prediction"]
