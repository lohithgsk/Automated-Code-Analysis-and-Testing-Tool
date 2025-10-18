import os
import subprocess
import tempfile
import json
import re
from typing import List, Tuple, Dict, Any
from pathlib import Path
import google.generativeai as genai
import textwrap
from dotenv import load_dotenv

load_dotenv()

# --- Gemini API Configuration ---
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY environment variable is not set. AI test generation will be skipped.", flush=True)
    else:
        genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error configuring Gemini API: {e}. AI test generation will be skipped.", flush=True)
    GEMINI_API_KEY = None


def run_testing_pipeline(code_files_content: List[str], file_paths: List[str]) -> Dict[str, Any]:
    """
    Orchestrates the entire testing pipeline and returns the final report,
    including any AI-generated test code.
    """
    print("\n" + "="*60, flush=True)
    print("--- Starting Automated Testing Pipeline ---", flush=True)

    final_report = {
        "summary": {}, "pynguin_test_generation": {"success": False, "message": "Pynguin step did not run."},
        "gemini_test_generation": {"success": False, "message": "Gemini step did not run."},
        "coverage_analysis": {"success": False, "message": "Coverage step did not run."},
        "mutation_testing": {"success": False, "message": "Mutation step did not run."}
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        print(f"Step 1: Creating temporary project structure at {project_root}", flush=True)
        
        try:
            source_paths, module_names = _setup_project_structure(project_root, code_files_content, file_paths)
            if not source_paths:
                raise ValueError("Setup failed: No valid Python modules found in selection.")
            
            tests_path = project_root / "tests"
            tests_path.mkdir()
            
            pynguin_report = _run_test_generation(project_root, tests_path, module_names)
            final_report["pynguin_test_generation"] = pynguin_report

            gemini_report = _run_ai_test_generation(tests_path, code_files_content, file_paths)
            final_report["gemini_test_generation"] = gemini_report
            
            if not pynguin_report.get("success") and not gemini_report.get("success"):
                 raise RuntimeError("All test generation methods failed, cannot proceed.")

            cov_report = _run_coverage_analysis(project_root, module_names)
            final_report["coverage_analysis"] = cov_report

            mut_report = _run_mutation_testing(project_root)
            final_report["mutation_testing"] = mut_report
            
            final_report["summary"] = {
                "overall_status": "Success", "message": "Testing pipeline completed.",
                "coverage": cov_report.get('summary', {}).get('percent_covered_display', 'N/A'),
                "mutation_score": mut_report.get('score', 'N/A')
            }

        except Exception as e:
            print(f"\n--- PIPELINE FAILED ---", flush=True)
            print(f"ERROR TYPE: {type(e).__name__}", flush=True)
            print(f"ERROR DETAILS: {e}", flush=True)
            final_report["summary"] = {"overall_status": "Failure", "message": str(e)}
        finally:
            print("\n--- Consolidated Testing Report ---", flush=True)
            print(json.dumps(final_report, indent=2), flush=True)
            print("="*60, flush=True)
            return final_report


def _setup_project_structure(root: Path, contents: List[str], paths: List[str]) -> Tuple[List[str], List[str]]:
    source_paths = []; module_names = []
    common_base = os.path.commonpath(paths) if paths else '.'
    for i, content in enumerate(contents):
        original_path = Path(paths[i])
        if original_path.suffix != ".py": continue
        relative_path = original_path.relative_to(Path(common_base))
        temp_path = root / relative_path
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(content, encoding='utf-8')
        source_paths.append(str(temp_path))
        module_name = ".".join(relative_path.with_suffix('').parts)
        module_names.append(module_name)
    for d in root.rglob('**/'):
        if d.is_dir(): (d / '__init__.py').touch()
    print(f"Recreated {len(module_names)} Python modules.", flush=True)
    return source_paths, module_names


def _run_test_generation(project_path: Path, output_path: Path, modules: List[str]) -> Dict[str, Any]:
    print("\nStep 2a: Generating unit tests with Pynguin...", flush=True)
    generated_files, errors = 0, []
    for module in modules:
        command = ["pynguin", "--project-path", str(project_path), "--output-path", str(output_path), "--module-name", module, "--maximum-search-time", "60"]
        print(f"Running for module: {module}", flush=True)
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            generated_files += 1; print(f"  -> Success for module {module}", flush=True)
        else:
            print(f"  -> Failure for module {module}", flush=True)
            errors.append({"module": module, "error": result.stderr[:500] + '...'})
    return {"tool": "Pynguin", "success": generated_files > 0, "modules_tested": len(modules), "test_suites_generated": generated_files, "errors": errors}


def _run_ai_test_generation(tests_path: Path, code_contents: List[str], file_paths: List[str]) -> Dict[str, Any]:
    print("\nStep 2b: Generating additional unit tests with Model...", flush=True)
    if not GEMINI_API_KEY: return {"tool": "Gemini", "success": False, "message": "GEMINI_API_KEY not set. Skipping."}
    
    model = genai.GenerativeModel('gemini-2.5-flash') 
    generation_config = genai.types.GenerationConfig(temperature=0.1, max_output_tokens=8192)
    safety_settings={'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE','HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE','HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE','HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',}
    
    generated_files, errors = 0, []
    generated_tests_data = [] # --- NEW: List to hold generated code ---

    for i, code in enumerate(code_contents):
        filename = os.path.basename(file_paths[i])
        print(f"Running for file: {filename}", flush=True)
        prompt = textwrap.dedent(f"""You are an expert Python developer...Python code to test:\n```python\n{code}\n```""") # Prompt omitted for brevity
        try:
            response = model.generate_content(prompt, generation_config=generation_config, safety_settings=safety_settings)
            
            if not response.candidates:
                block_reason = "Unknown"
                if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'): block_reason = response.prompt_feedback.block_reason.name
                raise ValueError(f"Response was blocked by safety filters. Reason: {block_reason}")

            test_code = response.text
            code_match = re.search(r'```python\n(.*)```', test_code, re.DOTALL)
            cleaned_code = code_match.group(1).strip() if code_match else test_code.strip()
            
            if cleaned_code:
                # --- NEW: Add the generated code to our list ---
                generated_tests_data.append({"filename": filename, "code": cleaned_code})

                test_file_path = tests_path / f"test_gemini_{filename}"
                test_file_path.write_text(cleaned_code, encoding='utf-8')
                generated_files += 1
                print(f"  -> Success for file {filename}", flush=True)
            else:
                raise ValueError("Gemini returned a valid but empty response.")
        except Exception as e:
            print(f"  -> Failure for file {filename}. Error: {e}", flush=True)
            errors.append({"file": filename, "error": str(e)})

    # --- NEW: Include the generated_tests list in the final report ---
    return {
        "tool": "Gemini", "success": generated_files > 0, "files_processed": len(code_contents), 
        "test_suites_generated": generated_files, "errors": errors, "generated_tests": generated_tests_data
    }


def _run_coverage_analysis(project_path: Path, modules: List[str]) -> Dict[str, Any]:
    print("\nStep 3: Running coverage analysis with pytest-cov...", flush=True)
    cov_json_path = project_path / "coverage.json"
    modules_to_cover = ",".join(m for m in modules if m)
    if not modules_to_cover: return {"tool": "pytest-cov", "success": False, "error": "No modules to cover."}
    command = ["pytest", f"--cov={modules_to_cover}", f"--cov-report=json:{cov_json_path}", str(project_path / "tests")]
    result = subprocess.run(command, capture_output=True, text=True, cwd=project_path, check=False)
    if cov_json_path.exists():
        with open(cov_json_path) as f: report = json.load(f)
        return {"tool": "pytest-cov", "success": True, "summary": report.get("totals", {}), "files": report.get("files", {})}
    else:
        return {"tool": "pytest-cov", "success": False, "error": result.stderr or result.stdout}

def _run_mutation_testing(project_path: Path) -> Dict[str, Any]:
    print("\nStep 4: Performing mutation testing with mutmut...", flush=True)
    (project_path / "setup.cfg").write_text("[mutmut]\npaths_to_mutate=.\nrunner=pytest\ntests_dir=tests\n")
    subprocess.run(["mutmut", "run", "--paths-to-mutate", "."], capture_output=True, text=True, cwd=project_path, check=False)
    result = subprocess.run(["mutmut", "results"], capture_output=True, text=True, cwd=project_path, check=False)
    lines, score = result.stdout.strip().split('\n'), "N/A"
    if lines and "killed" in lines[-1]:
        parts = lines[-1].split('(')
        if len(parts) > 1: score = parts[1].split(')')[0]
    return {"tool": "mutmut", "success": result.returncode == 0, "score": score, "raw_report": result.stdout}