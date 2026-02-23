import json
import os
from pathlib import Path

def load_gemini_config():
    """
    .gemini/config.json 파일을 로드합니다.
    """
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        print(f"Error: {config_path} not found.")
        return None
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_instructions():
    """
    .gemini/instructions.md 파일을 로드합니다.
    """
    instr_path = Path(__file__).parent / "instructions.md"
    if not instr_path.exists():
        print(f"Error: {instr_path} not found.")
        return None
    
    with open(instr_path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    print("--- Gemini 3.0 Loader Test ---")
    config = load_gemini_config()
    if config:
        print(f"Target Model: {config['models']['text']}")
        print(f"Temperature: {config['parameters']['temperature']}")
    
    instructions = load_instructions()
    if instructions:
        print("\n--- System Instructions Loaded ---")
        print(instructions[:100] + "...")
