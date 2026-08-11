# Model Checkpoint

The Python code expects a YOLO-compatible PyTorch checkpoint.

Default location:

```text
models/fire.pt
```

Alternative:

```text
MODEL_PATH=path/to/your/checkpoint.pt
```

The original repository contained `fire.pt`, but no training script, dataset manifest, or evaluation report was available to verify training methodology or accuracy. Keep large checkpoints and datasets out of Git unless you intentionally use Git LFS or provide a documented external download.
