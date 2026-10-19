# Model artifacts

This package contains an inference application with an explicit model contract. It does not include a verified pretrained classifier. See `models/README.md`.

No verified pretrained DDoS model, feature ordering, or scaler was available for this package. The interface and ONNX inference contract are implemented, but classification is disabled until matching trusted artifacts are installed. No scores or accuracy claims are fabricated. This is not a live packet monitor or automatic mitigation system.

Only install trusted artifacts. No private dataset, sample patient image, malicious executable, or fabricated metric is included.

## ONNX contract

Place the trusted fitted classifier at `models/model.onnx` and its metadata at
`models/schema.json`. The graph must include all preprocessing and accept one
float32 tensor with shape `[N, feature_count]`. It must expose an `[N, C]` tensor
of class probabilities, not logits or ONNX ZipMap dictionaries.

The schema must provide the exact feature names in order, the probability tensor
output name, and the attack class index. `schema.example.json` documents the
format only; its strings are not valid feature names for a real model. Missing,
extra, duplicate, nonnumeric, or nonfinite CSV features are rejected.

No generic traffic columns are assumed because incompatible feature units,
ordering, or scalers would make predictions misleading. Artifact installation
is required; this package does not ask the operator to fit a new model.
