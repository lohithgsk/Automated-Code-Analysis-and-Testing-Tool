import subprocess
import os
import tempfile
from pathlib import Path

def create_ollama_model(base_model: str, adapter_path: str, custom_model_name: str):
    """
    Automates the creation of a new Ollama model with a finetuned adapter.

    Args:
        base_model (str): The name of the base model in Ollama (e.g., 'deepseek-coder:latest').
        adapter_path (str): The path to the directory containing the finetuned adapter.
        custom_model_name (str): The desired name for the new Ollama model.
    """
    print("\n" + "="*50)
    print("--- Starting Ollama Integration ---")
    print(f"Custom model name: {custom_model_name}")
    print(f"Base model: {base_model}")
    
    # Ensure the adapter path is absolute
    absolute_adapter_path = Path(adapter_path).resolve()
    print(f"Adapter path: {absolute_adapter_path}")

    if not absolute_adapter_path.exists():
        print(f"ERROR: Adapter directory not found at {absolute_adapter_path}")
        return

    # 1. Create the Modelfile content
    modelfile_content = f"""
FROM {base_model}
ADAPTER {absolute_adapter_path}
"""
    print("\nStep 1: Generating Modelfile content:")
    print("-" * 20)
    print(modelfile_content.strip())
    print("-" * 20)

    # 2. Use a temporary file for the Modelfile
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.Modelfile') as tmp_modelfile:
            tmp_modelfile.write(modelfile_content)
            tmp_modelfile_path = tmp_modelfile.name
        
        print(f"\nStep 2: Modelfile temporarily saved to {tmp_modelfile_path}")

        # 3. Run the 'ollama create' command
        command = ["ollama", "create", custom_model_name, "-f", tmp_modelfile_path]
        print(f"\nStep 3: Running command: {' '.join(command)}")

        # Use Popen to stream the output in real-time
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')

        print("\n--- Ollama Output ---")
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        rc = process.poll()
        print("--- End Ollama Output ---")

        if rc == 0:
            print(f"\nSuccess! Your new model '{custom_model_name}' has been created in Ollama.")
            print(f"   You can now run it with: ollama run {custom_model_name}")
        else:
            print(f"\nFailure. 'ollama create' command failed with return code {rc}.")
            print("   Please check the output above for errors.")

    except FileNotFoundError:
        print("\nFATAL ERROR: The 'ollama' command was not found.")
        print("   Please ensure Ollama is installed and that its command is in your system's PATH.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # 4. Clean up the temporary file
        if 'tmp_modelfile_path' in locals() and os.path.exists(tmp_modelfile_path):
            os.remove(tmp_modelfile_path)
            print(f"\nStep 4: Cleaned up temporary Modelfile.")
    
    print("--- Ollama Integration Finished ---")

if __name__ == '__main__':
    # For direct testing of this script
    # Make sure you have a finetuned adapter in the specified directory
    print("Running ollama_integration.py directly for testing.")
    create_ollama_model(
        base_model="deepseek-coder:latest",
        adapter_path="./deepseek-coder-custom-adapter", # CHANGE THIS to your adapter path
        custom_model_name="my-test-coder"
    )