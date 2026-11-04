"""
Ojas CLI Prototype Runner.

This interactive CLI tests and showcases the capabilities of your local model (ojas.gguf):
1. Speed & Hardware Benchmark (load time, tokens/sec, memory).
2. Interactive Code Assistant (stream responses live).
3. Automated Dev -> Test -> Fix Loop (real pytest validation & self-healing).
"""

import ast
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Set up project root and path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

# Safe UTF-8 console output for Windows terminal
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from backend.app.llm.llama_cpp_client import LlamaCppClient
from backend.app.config import get_settings


# ── ANSI Terminal Colors ──────────────────────────────────────────────────
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


def print_banner():
    banner = f"""
{Color.CYAN}{Color.BOLD}======================================================================
               OJAS — LOCAL AI AGENT CLI PROTOTYPE
  Fully Offline Software Development & Automated Self-Healing Loop
======================================================================{Color.RESET}
"""
    print(banner)


# ── Code Extraction Helper ────────────────────────────────────────────────
def extract_python_code(text: str) -> str:
    """Extract code from ```python ... ``` or return clean code."""
    pattern = r"```(?:python)?\s*([\s\S]*?)```"
    matches = re.findall(pattern, text)
    if matches:
        return matches[0].strip()
    # Fallback: if no code block was used, return raw text stripped
    return text.strip()


def validate_python_syntax(code: str) -> tuple[bool, str]:
    """Check if Python syntax is valid using AST parse."""
    try:
        ast.parse(code)
        return True, "Syntax is valid."
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"


# ── Mode 1: Benchmark ─────────────────────────────────────────────────────
def run_benchmark(client: LlamaCppClient):
    print(f"\n{Color.YELLOW}[*] Running Model Benchmark...{Color.RESET}")
    info = client.get_info()
    print(f"  • Model file:        {Color.BOLD}{info.get('model_name')}{Color.RESET}")
    print(f"  • Context window:    {info.get('context_size')} tokens")
    print(f"  • Model load time:   {info.get('load_time_seconds')} seconds")

    test_prompt = "Write a Python function named `fibonacci(n)` that returns the first n Fibonacci numbers."
    print(f"\n  • Benchmark prompt: {Color.CYAN}{test_prompt}{Color.RESET}")
    print(f"  • Generating tokens...\n")

    start_time = time.perf_counter()
    token_count = 0

    print(f"{Color.GREEN}", end="")
    for token in client.stream(test_prompt, max_tokens=180, temperature=0.2):
        print(token, end="", flush=True)
        token_count += 1
    print(f"{Color.RESET}\n")

    total_time = time.perf_counter() - start_time
    tps = token_count / total_time if total_time > 0 else 0

    print(f"{Color.BOLD}--- Benchmark Results ---{Color.RESET}")
    print(f"  • Tokens generated:  {token_count}")
    print(f"  • Total time:        {total_time:.2f} s")
    print(f"  • Generation speed:  {Color.GREEN}{Color.BOLD}{tps:.2f} tokens/second{Color.RESET}")
    print(f"-------------------------\n")


# ── Mode 2: Interactive Prompt ────────────────────────────────────────────
def run_interactive(client: LlamaCppClient):
    print(f"\n{Color.YELLOW}[*] Interactive Coding Assistant Mode{Color.RESET}")
    print("Type your requirement or prompt (or type 'exit' to return to menu):\n")

    system_prompt = (
        "You are Ojas, an expert offline Python software development assistant. "
        "Provide direct, clean, and bug-free Python code with clear explanations."
    )

    while True:
        try:
            user_input = input(f"{Color.BLUE}Ojas >> {Color.RESET}").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                break

            print(f"\n{Color.GREEN}", end="")
            for token in client.stream(
                f"<|system|>\n{system_prompt}\n<|user|>\n{user_input}\n<|assistant|>\n",
                max_tokens=600,
                temperature=0.2,
            ):
                print(token, end="", flush=True)
            print(f"{Color.RESET}\n")

        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            break


# ── Mode 3: Autonomous Dev -> Test -> Fix Loop ───────────────────────────
SAMPLE_SPEC = """
Create a Python class named `Calculator` with the following methods:
1. `add(a, b)`: returns the sum of a and b.
2. `subtract(a, b)`: returns a minus b.
3. `multiply(a, b)`: returns a multiplied by b.
4. `divide(a, b)`: returns a divided by b. If b is 0, raises ValueError("Cannot divide by zero").
5. `power(a, b)`: returns a raised to the power of b.
Return ONLY valid Python code inside ```python ... ``` block.
"""

SAMPLE_TESTS = """import pytest
from calculator import Calculator

def test_add():
    calc = Calculator()
    assert calc.add(10, 5) == 15
    assert calc.add(-2, 2) == 0

def test_subtract():
    calc = Calculator()
    assert calc.subtract(10, 5) == 5
    assert calc.subtract(0, 7) == -7

def test_multiply():
    calc = Calculator()
    assert calc.multiply(4, 3) == 12
    assert calc.multiply(5, 0) == 0

def test_divide():
    calc = Calculator()
    assert calc.divide(10, 2) == 5.0
    with pytest.raises(ValueError):
        calc.divide(10, 0)

def test_power():
    calc = Calculator()
    assert calc.power(2, 3) == 8
    assert calc.power(5, 0) == 1
"""


def run_auto_fix_loop(client: LlamaCppClient):
    print(f"\n{Color.YELLOW}[*] Autonomous Dev -> Test -> Fix Loop Demo{Color.RESET}")
    print("Testing Ojas core architecture:")
    print("  1. Agent analyzes requirements and generates Python module.")
    print("  2. Static AST check validates code structure.")
    print("  3. Real pytest runs against user-defined tests.")
    print("  4. If tests fail, Agent receives error traceback and fixes the bug automatically.\n")

    workspace = PROJECT_ROOT / "workspace"
    workspace.mkdir(exist_ok=True)

    code_file = workspace / "calculator.py"
    test_file = workspace / "test_calculator.py"

    # Write the pytest file into workspace
    test_file.write_text(SAMPLE_TESTS, encoding="utf-8")
    print(f"{Color.CYAN}[1/4] Test suite prepared at: workspace/test_calculator.py{Color.RESET}")

    # Generate initial code
    prompt = (
        f"<|system|>\nYou are an expert Python developer. Write clean, complete code.\n"
        f"<|user|>\nRequirement:\n{SAMPLE_SPEC}\n<|assistant|>\n"
    )

    print(f"{Color.CYAN}[2/4] Development Agent generating initial code...{Color.RESET}")
    initial_response = client.generate(prompt, max_tokens=600, temperature=0.2)
    code = extract_python_code(initial_response)

    # Static AST check
    is_valid, msg = validate_python_syntax(code)
    if not is_valid:
        print(f"{Color.RED}[!] Initial code syntax error: {msg}{Color.RESET}")
    else:
        print(f"{Color.GREEN}[✓] Static AST syntax check: PASSED{Color.RESET}")

    code_file.write_text(code, encoding="utf-8")
    print(f"    Saved generated code to: {code_file.name}")

    # Iteration loop (up to 3 iterations)
    max_iterations = 3
    success = False
    python_exe = str(PROJECT_ROOT / "runtime" / "venv" / "Scripts" / "python.exe")

    for iteration in range(1, max_iterations + 1):
        print(f"\n{Color.BOLD}--- Iteration {iteration}/{max_iterations}: Running Pytest ---{Color.RESET}")

        # Run pytest via subprocess
        proc = subprocess.run(
            [python_exe, "-m", "pytest", str(test_file), "-v", "--tb=short"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )

        if proc.returncode == 0:
            print(f"{Color.GREEN}{Color.BOLD}[✓] ALL TESTS PASSED!{Color.RESET}")
            print(proc.stdout)
            success = True
            break
        else:
            print(f"{Color.RED}[✗] Tests Failed on iteration {iteration}:{Color.RESET}")
            # Display test failure snippet
            lines = proc.stdout.splitlines()
            for line in lines[-15:]:
                print(f"    {line}")

            if iteration == max_iterations:
                print(f"\n{Color.RED}Reached max iteration limit ({max_iterations}). Escalating to user.{Color.RESET}")
                break

            # Self-healing fix request
            print(f"\n{Color.YELLOW}[*] Testing Agent feeding traceback to Development Agent for fixing...{Color.RESET}")
            fix_prompt = (
                f"<|system|>\nYou are an expert Python debugging agent. Analyze the failed test traceback and fix the code.\n"
                f"<|user|>\n"
                f"CURRENT CODE:\n```python\n{code}\n```\n\n"
                f"PYTEST TRACEBACK:\n{proc.stdout}\n\n"
                f"Fix the bug so all tests pass. Return ONLY the complete corrected Python code inside a ```python ... ``` block.\n"
                f"<|assistant|>\n"
            )

            fixed_response = client.generate(fix_prompt, max_tokens=700, temperature=0.1)
            code = extract_python_code(fixed_response)
            code_file.write_text(code, encoding="utf-8")
            print(f"{Color.CYAN}    Applied auto-fix to {code_file.name}. Re-testing...{Color.RESET}")

    print(f"\n{Color.BOLD}=== Summary ==={Color.RESET}")
    if success:
        print(f"{Color.GREEN}Demonstration Succeeded: Local model autonomously wrote code, satisfied requirements, and passed all tests!{Color.RESET}")
    else:
        print(f"{Color.YELLOW}Demonstration Finished: Check workspace/calculator.py to review the generated code.{Color.RESET}")


# ── Main Menu ─────────────────────────────────────────────────────────────
def main():
    print_banner()

    print("Checking environment & model...")
    try:
        client = LlamaCppClient()
    except Exception as e:
        print(f"{Color.RED}[!] Error loading LLM client: {e}{Color.RESET}")
        return

    if not client.is_loaded():
        info = client.get_info()
        print(f"{Color.RED}[!] Model is NOT loaded! Error: {info.get('last_error')}{Color.RESET}")
        print("Please ensure models/ojas.gguf is present.")
        return

    info = client.get_info()
    print(f"{Color.GREEN}[✓] Model Ready: {info.get('model_name')} (Loaded in {info.get('load_time_seconds')}s){Color.RESET}")

    while True:
        print(f"\n{Color.BOLD}Select an Option:{Color.RESET}")
        print("  1. Run Speed & Hardware Benchmark (Tokens/sec, Latency)")
        print("  2. Interactive Coding Mode (Chat & live code streaming)")
        print("  3. Run Autonomous Dev -> Test -> Fix Loop (The Ojas Core Demo)")
        print("  4. View Model & Environment Details")
        print("  5. Exit")

        choice = input(f"\n{Color.CYAN}Enter choice [1-5]: {Color.RESET}").strip()

        if choice == "1":
            run_benchmark(client)
        elif choice == "2":
            run_interactive(client)
        elif choice == "3":
            run_auto_fix_loop(client)
        elif choice == "4":
            print(f"\n{Color.BOLD}Model Details:{Color.RESET}")
            for k, v in client.get_info().items():
                print(f"  • {k}: {v}")
            settings = get_settings()
            print(f"  • Threads: {settings.n_threads}, Batch: {settings.n_batch}, Max Tokens: {settings.max_tokens}")
        elif choice == "5":
            print("\nExiting Ojas Prototype. Goodbye!")
            break
        else:
            print(f"{Color.RED}Invalid option. Please enter 1 to 5.{Color.RESET}")


if __name__ == "__main__":
    main()

