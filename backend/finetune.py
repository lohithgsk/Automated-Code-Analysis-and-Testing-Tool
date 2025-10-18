import os
import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig, prepare_model_for_kbit_training, get_peft_model
from trl import SFTTrainer
from typing import List

# Import the new Ollama integration function
from ollama_integration import create_ollama_model

# --- Configuration ---
BASE_MODEL_ID = "deepseek-ai/deepseek-coder-1.3b-base"
# The base directory for saving adapter outputs
ADAPTER_OUTPUT_BASE_DIR = "./finetuned_adapters"

# The function signature is correct and accepts both arguments
def start_finetuning(code_files_content: List[str], ollama_model_name: str):
    """
    Main function to start the finetuning process and then integrate with Ollama.
    """
    print("--- Starting Finetuning Process ---")

    # Dynamic output directory for the adapter based on the ollama model name
    output_dir = os.path.join(ADAPTER_OUTPUT_BASE_DIR, ollama_model_name)
    print(f"Adapter will be saved to: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    # Pre-check for CUDA
    if not torch.cuda.is_available():
        error_message = (
            "FATAL: No CUDA-enabled GPU found or PyTorch is not installed with CUDA support."
        )
        print(error_message)
        raise RuntimeError(error_message)
    
    print(f"GPU detected: {torch.cuda.get_device_name(0)}")

    # 1. Prepare the dataset
    print(f"Step 1: Preparing dataset with {len(code_files_content)} files.")
    dataset_dict = {'text': code_files_content}
    dataset = Dataset.from_dict(dataset_dict)
    print("Dataset prepared successfully.")

    # 2. Configure Quantization (QLoRA)
    print("Step 2: Configuring 4-bit quantization.")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )
    print("Quantization configured.")

    # 3. Load the Model and Tokenizer
    print(f"Step 3: Loading base model ('{BASE_MODEL_ID}') and tokenizer.")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    print("Model and tokenizer loaded.")

    # 4. Configure LoRA
    print("Step 4: Configuring LoRA.")
    model = prepare_model_for_kbit_training(model)
    lora_config = LoraConfig(
        r=8,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    print("LoRA configured.")

    # 5. Configure Training Arguments
    print("Step 5: Setting up training arguments.")
    training_args = TrainingArguments(
        output_dir=output_dir, # Use the dynamic output directory
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        num_train_epochs=3,
        logging_steps=10,
        save_strategy="epoch",
        fp16=True,
        push_to_hub=False,
    )
    print("Training arguments set.")

    # 6. Initialize the Trainer and Start Training
    print("Step 6: Initializing SFTTrainer and starting training.")
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=lora_config,
        dataset_text_field="text",
        max_seq_length=1024,
        tokenizer=tokenizer,
        args=training_args,
    )

    trainer.train()
    print("--- Training Completed ---")

    # 7. Save the final LoRA adapter
    print(f"Step 7: Saving the finetuned LoRA adapter to '{output_dir}'.")
    trainer.save_model(output_dir)
    print("--- Finetuning Process Finished Successfully ---")
    
    # 8. --- NEW: Automatically integrate with Ollama ---
    create_ollama_model(
        base_model="deepseek-coder:latest",
        adapter_path=output_dir,
        custom_model_name=ollama_model_name
    )

if __name__ == '__main__':
    print("Running finetune.py directly for testing purposes.")

    #THESE ARE JUST MOCK FILE CONTENTS FOR TESTING
    mock_code_files = [
        "def hello_world():\n    print('Hello from file 1!')",
        "def add(a, b):\n    # A simple function to add two numbers\n    return a + b",
        "class Calculator:\n    def multiply(self, x, y):\n        return x * y"
    ]
    try:
        start_finetuning(mock_code_files, "my-direct-test-coder")
    except RuntimeError as e:
        print(e)