import subprocess
import json
import tempfile
import os
from typing import List, Dict, Any
from radon.complexity import cc_visit
from radon.metrics import mi_visit



def analyze_codebase(code_files_content: List[str], file_paths: List[str]) -> Dict[str, Any]:
    """
    Orchestrates the analysis of a list of code files and returns a structured report.
    """
    print("--- Starting Code Analysis Preprocessing Layer ---")

    # Use temporary files to run external tools like bandit
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_paths = []
        for i, content in enumerate(code_files_content):
            # Try to get the original filename, otherwise use a generic name
            original_filename = os.path.basename(file_paths[i]) if i < len(file_paths) else f"file_{i}.py"
            temp_path = os.path.join(temp_dir, original_filename)
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            temp_file_paths.append(temp_path)

        security_results = _run_security_scan(temp_dir)
        quality_results = _run_quality_check(code_files_content)
        # Placeholder for dependency analysis
        dependency_results = {"score": 75, "summary": "Dependency analysis not yet implemented."}

    # Generate the final matrix chart
    matrix_chart = _generate_matrix_chart(security_results, quality_results, dependency_results)
    
    print("--- Code Analysis Finished ---")
    return matrix_chart


def _run_security_scan(directory: str) -> Dict[str, Any]:
    """
    Runs Bandit security scanner on a directory of code files.
    """
    print("Step 1: Running security scan with Bandit...")
    command = [
        "bandit",
        "-r", directory,
        "-f", "json"
    ]
    try:
        # Run bandit as a subprocess
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        
        if result.returncode == 0 or result.returncode == 1: # Bandit exits 1 if issues found
            try:
                report = json.loads(result.stdout)
                
                high_sev = report['metrics']['_totals']['SEVERITY.HIGH']
                medium_sev = report['metrics']['_totals']['SEVERITY.MEDIUM']
                low_sev = report['metrics']['_totals']['SEVERITY.LOW']

                # Simple scoring: 100 is perfect. Penalize for vulnerabilities.
                score = 100 - (high_sev * 10) - (medium_sev * 5) - (low_sev * 2)
                score = max(0, score) # Ensure score doesn't go below 0

                summary = (
                    f"Found {high_sev} high, {medium_sev} medium, "
                    f"and {low_sev} low severity issues."
                )
                
                return {
                    "score": score,
                    "summary": summary,
                    "details": report['results']
                }

            except json.JSONDecodeError:
                return {"score": 0, "summary": "Error parsing Bandit JSON output.", "details": result.stdout}
        else:
             return {"score": 0, "summary": "Bandit command failed to execute.", "details": result.stderr}

    except FileNotFoundError:
        return {"score": 0, "summary": "Bandit command not found. Is it installed?", "details": ""}
    except Exception as e:
        return {"score": 0, "summary": f"An unexpected error occurred during security scan: {e}", "details": ""}


def _run_quality_check(code_contents: List[str]) -> Dict[str, Any]:
    """
    Runs Radon for code quality metrics (Cyclomatic Complexity and Maintainability Index).
    """
    print("Step 2: Running code quality checks with Radon...")
    total_complexity = 0
    total_mi_score = 0
    function_count = 0
    complex_functions = []

    for code in code_contents:
        try:
            # Cyclomatic Complexity
            complexity_results = cc_visit(code)
            for item in complexity_results:
                if item.complexity > 10: # Threshold for high complexity
                    complex_functions.append(f"{item.name} (Complexity: {item.complexity})")
                total_complexity += item.complexity
                function_count += 1
            
            # Maintainability Index
            mi_score = mi_visit(code, multi=True)
            if mi_score > 0:
                total_mi_score += mi_score
        except Exception:
            # Ignore files that Radon can't parse
            continue

    avg_complexity = (total_complexity / function_count) if function_count > 0 else 0
    avg_mi = (total_mi_score / len(code_contents)) if code_contents else 0

    # Scoring: Lower complexity is better, higher MI is better.
    # Normalize scores to be out of 100.
    complexity_score = max(0, 100 - (avg_complexity - 5) * 10) # Target avg complexity of <= 5
    mi_score_normalized = (avg_mi / 100) * 100 if avg_mi > 0 else 100

    overall_quality_score = (complexity_score + mi_score_normalized) / 2
    
    summary = (
        f"Average Cyclomatic Complexity: {avg_complexity:.2f}. "
        f"Average Maintainability Index: {avg_mi:.2f}. "
        f"{len(complex_functions)} functions are overly complex."
    )

    return {
        "score": round(overall_quality_score),
        "summary": summary,
        "details": {
            "average_complexity": f"{avg_complexity:.2f}",
            "average_maintainability_index": f"{avg_mi:.2f}",
            "highly_complex_functions": complex_functions
        }
    }


def _generate_matrix_chart(security: Dict, quality: Dict, dependency: Dict) -> Dict[str, Any]:
    """
    Generates the final matrix chart from the analysis results.
    """
    print("Step 3: Generating final analysis matrix chart...")
    
    # Define grading scales
    def get_grade(score):
        if score >= 90: return "A (Excellent)"
        if score >= 75: return "B (Good)"
        if score >= 60: return "C (Fair)"
        if score >= 40: return "D (Poor)"
        return "F (Critical)"

    matrix = {
        "title": "Code Analysis Report",
        "overall_score": round((security['score'] + quality['score'] + dependency['score']) / 3),
        "categories": [
            {
                "name": "Security Scan",
                "score": security['score'],
                "grade": get_grade(security['score']),
                "summary": security['summary'],
                "explanation": "Scans for common security vulnerabilities like hardcoded passwords, SQL injection, and insecure library usage. Score is penalized based on the severity of issues found.",
                "recommendations": "Review high and medium severity issues from the details below. Use a secret manager for credentials. Sanitize all user inputs.",
                "details": security['details']
            },
            {
                "name": "Code Quality",
                "score": quality['score'],
                "grade": get_grade(quality['score']),
                "summary": quality['summary'],
                "explanation": "Measures code maintainability and complexity. High Cyclomatic Complexity makes code hard to test and understand. A high Maintainability Index is desirable.",
                "recommendations": "Refactor functions with high complexity (>10) into smaller, more focused units. Improve documentation and simplify control flow.",
                "details": quality['details']
            },
            {
                "name": "Dependency Analysis",
                "score": dependency['score'],
                "grade": get_grade(dependency['score']),
                "summary": dependency['summary'],
                "explanation": "Checks project dependencies for known vulnerabilities and outdated packages. Keeping dependencies up-to-date is crucial for security.",
                "recommendations": "Implement a tool like `pip-audit` or GitHub's Dependabot to automate dependency scanning. Regularly update packages to their latest stable versions.",
                "details": {} # Placeholder
            }
        ]
    }
    return matrix