import os
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Import analysis, finetuning, and testing functions
from finetune import start_finetuning
from code_analyzer import analyze_codebase
from code_tester import run_testing_pipeline

# Initialize the FastAPI app
app = FastAPI(
    title="Code Analysis and Testing Tool API",
    description="APIs for file import, code analysis, testing, and model finetuning.",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class DirectoryPathRequest(BaseModel):
    path: str

class FileSelectionRequest(BaseModel):
    base_path: str
    selected_items: List[str]
    ollama_model_name: Optional[str] = Field("custom-deepseek-coder")

class OllamaChatRequest(BaseModel):
    model: str
    prompt: str

# --- Helper Functions (Omitted for Brevity) ---
def get_directory_tree(path: str) -> Dict[str, Any]:
    # ...
    if not os.path.isdir(path): raise ValueError("Provided path is not a valid directory.")
    tree = {'name': os.path.basename(path), 'path': path, 'type': 'folder', 'children': []}
    try:
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path): tree['children'].append(get_directory_tree(item_path))
            else: tree['children'].append({'name': item, 'path': item_path, 'type': 'file'})
    except OSError as e: print(f"Error accessing {path}: {e}")
    return tree

def get_code_from_selection(base_path: str, selected_items: List[str]) -> Tuple[List[str], List[str]]:
    # ...
    code_files_content, file_paths = [], []
    if not os.path.isdir(base_path): raise HTTPException(status_code=404, detail="Base directory not found.")
    for item_path in selected_items:
        if not os.path.exists(item_path): continue
        files_to_read = []
        if os.path.isfile(item_path): files_to_read.append(item_path)
        elif os.path.isdir(item_path):
            for root, _, files in os.walk(item_path):
                for name in files: files_to_read.append(os.path.join(root, name))
        for file_path in files_to_read:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code_files_content.append(f.read()); file_paths.append(file_path)
            except Exception as e: print(f"Warning: Could not read file {file_path}. Error: {e}")
    return code_files_content, file_paths

# --- API Endpoints ---
@app.post("/api/v1/list-directory")
def list_directory_contents(request: DirectoryPathRequest):
    try:
        if not os.path.isdir(request.path): raise HTTPException(status_code=404, detail="Directory not found.")
        return get_directory_tree(request.path)
    except Exception as e: raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post("/api/v1/code-analysis-report")
def get_code_analysis_report(request: FileSelectionRequest):
    code_contents, file_paths = get_code_from_selection(request.base_path, request.selected_items)
    if not code_contents: raise HTTPException(status_code=400, detail="No readable code files found.")
    return analyze_codebase(code_contents, file_paths)

@app.post("/api/v1/run-testing-pipeline")
def automated_testing(request: FileSelectionRequest):
    code_contents, file_paths = get_code_from_selection(request.base_path, request.selected_items)
    if not any(f.endswith('.py') for f in file_paths): raise HTTPException(status_code=400, detail="No Python files found.")
    return run_testing_pipeline(code_files_content=code_contents, file_paths=file_paths)

@app.post("/api/v1/finetune")
def finetune_model_on_files(request: FileSelectionRequest, background_tasks: BackgroundTasks):
    code_files_content, _ = get_code_from_selection(request.base_path, request.selected_items)
    if not code_files_content: raise HTTPException(status_code=400, detail="No readable code files found.")
    background_tasks.add_task(start_finetuning, code_files_content, request.ollama_model_name)
    return {"message": "Finetuning process started.", "files_for_training": len(code_files_content)}

# --- NEW OLLAMA ENDPOINTS ---
@app.get("/api/v1/ollama/models", summary="List Local Ollama Models")
def list_ollama_models():
    """Fetches the list of models available locally from the Ollama API."""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        response.raise_for_status()
        return response.json().get("models", [])
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not connect to Ollama: {e}")

def ollama_streamer(model: str, prompt: str):
    """Generator function to stream Ollama responses."""
    try:
        payload = {"model": model, "prompt": prompt, "stream": True}
        response = requests.post("http://localhost:11434/api/generate", json=payload, stream=True)
        response.raise_for_status()
        for chunk in response.iter_lines():
            if chunk:
                data = json.loads(chunk)
                yield json.dumps({"token": data.get("response", "")}) + "\n"
    except requests.exceptions.RequestException as e:
        yield json.dumps({"error": f"Ollama API error: {e}"}) + "\n"

@app.post("/api/v1/ollama/chat", summary="Chat with an Ollama Model")
def chat_with_ollama(request: OllamaChatRequest):
    """Streams a response from a specified Ollama model based on a prompt."""
    return StreamingResponse(ollama_streamer(request.model, request.prompt), media_type="application/x-ndjson")