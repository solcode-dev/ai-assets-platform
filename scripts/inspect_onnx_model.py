import onnxruntime as ort
import os

model_path = "/app/storage/model_cache/model.onnx"

if not os.path.exists(model_path):
    print(f"❌ Model file found at {model_path}")
    exit(1)

sess = ort.InferenceSession(model_path)

print("=== Inputs ===")
for i in sess.get_inputs():
    print(f"Name: {i.name}, Shape: {i.shape}, Type: {i.type}")

print("\n=== Outputs ===")
for o in sess.get_outputs():
    print(f"Name: {o.name}, Shape: {o.shape}, Type: {o.type}")
