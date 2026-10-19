from pathlib import Path
from functools import lru_cache
import json
import csv
import io
from src.validation import check_bytes, validate_rows, threshold_value
BASE = Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def load_model():
    import onnxruntime as ort
    model_path = BASE / "models/model.onnx"
    schema_path = BASE / "models/schema.json"
    if not model_path.is_file() or not schema_path.is_file():
        raise FileNotFoundError("A verified DDoS ONNX classifier and matching schema.json are not installed. No predictions have been generated.")
    schema = json.loads(schema_path.read_text())
    if schema.get("preprocessing") != "embedded_in_onnx":
        raise ValueError("All scaling and preprocessing must be embedded in the ONNX graph.")
    features = schema.get("features", [])
    if not features or not all(isinstance(f,str) and f for f in features) or len(set(features)) != len(features):
        raise ValueError("Invalid feature names.")
    if schema.get("score_semantics") != "attack_probability":
        raise ValueError("Output must explicitly represent attack probability.")
    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    inputs = session.get_inputs()
    if len(inputs) != 1 or inputs[0].type != "tensor(float)":
        raise ValueError("Expected one float32 tensor input.")
    shape = inputs[0].shape
    if len(shape) != 2 or (isinstance(shape[1],int) and shape[1] != len(features)):
        raise ValueError("Model input shape does not match schema.")
    return session, schema

def predict_csv(data, threshold=0.5):
    import numpy as np
    check_bytes(data)
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("Missing or duplicate CSV columns.")
    rows = list(reader)
    if len(rows) > 10000: raise ValueError("Maximum 10,000 flow records per batch.")
    session, schema = load_model()
    values = np.asarray(validate_rows(rows,schema["features"]),dtype=np.float32)
    if not np.isfinite(values).all(): raise ValueError("Float32 overflow in input.")
    outputs = session.run([schema["probability_output"]], {session.get_inputs()[0].name: values})[0]
    scores = np.asarray(outputs)
    index = schema.get("attack_class_index", 1)
    if scores.ndim != 2 or scores.shape[0] != len(rows) or not isinstance(index,int) or not 0 <= index < scores.shape[1]:
        raise ValueError("Expected an N-by-C probability tensor and valid attack_class_index.")
    if not np.isfinite(scores).all() or (scores < 0).any() or (scores > 1).any():
        raise ValueError("Invalid model probabilities.")
    threshold = threshold_value(threshold)
    return {"records": [{"row": i+1, "attack_score": float(score),
                         "label": "DDoS risk" if score >= threshold else "lower-risk"}
                        for i,score in enumerate(scores[:,index])],
            "notice": "Offline flow classification only; no traffic is generated or blocked."}
