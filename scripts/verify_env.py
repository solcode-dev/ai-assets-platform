import sys
import importlib

def check_package(package_name):
    try:
        pkg = importlib.import_module(package_name)
        version = getattr(pkg, '__version__', 'unknown')
        print(f"✅ {package_name} installed. Version: {version}")
        return True
    except ImportError as e:
        print(f"❌ {package_name} NOT installed. Error: {e}")
        return False

def check_onnx_runtime():
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        print(f"✅ onnxruntime available. Providers: {providers}")
        if 'CPUExecutionProvider' not in providers:
            print("⚠️ CPUExecutionProvider not found. This might inevitably cause issues on CPU environment.")
        return True
    except ImportError:
        print("❌ onnxruntime import failed.")
        return False

def main():
    print("--- 🛠️ AI/ML Environment Verification ---")
    packages = ["optimum", "onnxruntime", "sentence_transformers", "pgvector"]
    all_pass = True
    
    for p in packages:
        if not check_package(p):
            all_pass = False
            
    if not check_onnx_runtime():
        all_pass = False
        
    if all_pass:
        print("\n🎉 All ML dependencies are ready!")
        sys.exit(0)
    else:
        print("\n⚠️ Some dependencies are missing. Please check requirements.txt and rebuild.")
        sys.exit(1)

if __name__ == "__main__":
    main()
