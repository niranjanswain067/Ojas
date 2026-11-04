"""
Ojas Universal Multi-Language CLI Prototype.

Supports ALL major programming languages and technologies:
Python, JavaScript/TypeScript, Java, C/C++, Go, Rust, C#, PHP, Web (HTML/CSS), SQL, etc.

Capabilities:
1. Universal Hardware & Speed Benchmark.
2. Polyglot Interactive Assistant (Any language/framework).
3. Autonomous Dev -> Test -> Fix Loop (Python & Node.js).
4. Universal Code Doctor: Upload/inspect ANY language file, detect bugs,
   generate native unit tests, and produce corrected code.
"""

import ast
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

# Safe UTF-8 output
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from backend.app.llm.llama_cpp_client import LlamaCppClient
from backend.app.config import get_settings


# ── ANSI Colors ───────────────────────────────────────────────────────────
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
               OJAS — UNIVERSAL AI AGENT CLI PROTOTYPE
  Multi-Language Support: Python | JS/TS | Java | C/C++ | Go | Rust | C#
  Offline Code Generation, Multi-Language Bug Detection & Testing
======================================================================{Color.RESET}
"""
    print(banner)


# ── Language Detection & Mapping ──────────────────────────────────────────
LANGUAGE_MAP = {
    ".py": {"name": "Python", "framework": "pytest", "runner": "pytest"},
    ".js": {"name": "JavaScript (Node.js)", "framework": "Node Test / Jest", "runner": "node"},
    ".ts": {"name": "TypeScript", "framework": "Vitest / Jest", "runner": "node"},
    ".java": {"name": "Java", "framework": "JUnit 5", "runner": "javac"},
    ".cpp": {"name": "C++", "framework": "GoogleTest / Catch2", "runner": "g++"},
    ".cc": {"name": "C++", "framework": "GoogleTest", "runner": "g++"},
    ".c": {"name": "C", "framework": "Unity / CTest", "runner": "gcc"},
    ".cs": {"name": "C# (.NET)", "framework": "xUnit / NUnit", "runner": "dotnet"},
    ".go": {"name": "Go", "framework": "go test", "runner": "go"},
    ".rs": {"name": "Rust", "framework": "cargo test", "runner": "rustc"},
    ".php": {"name": "PHP", "framework": "PHPUnit", "runner": "php"},
    ".html": {"name": "HTML / Web", "framework": "W3C Validator / Playwright", "runner": None},
    ".sql": {"name": "SQL", "framework": "SQL Linter", "runner": None},
}


def detect_language(file_path: Path) -> dict:
    ext = file_path.suffix.lower()
    return LANGUAGE_MAP.get(ext, {"name": "Generic Code", "framework": "Unit Tests", "runner": None})


def extract_code_block(text: str, default_lang: str = "") -> str:
    """Extract code from ```lang ... ``` or return stripped text."""
    pattern = r"```(?:\w+)?\s*([\s\S]*?)```"
    matches = re.findall(pattern, text)
    if matches:
        return matches[0].strip()
    return text.strip()


# ── Built-in Multi-Language Buggy Samples ─────────────────────────────────
SAMPLES = {
    "1": {
        "title": "JavaScript (Node.js) - Async & Cart Calculation Bug",
        "filename": "shoppingCart.js",
        "lang": "javascript",
        "code": """// Shopping Cart with common JS async & floating point bugs
class ShoppingCart {
    constructor() {
        this.items = [];
    }

    addItem(name, price, quantity) {
        // BUG 1: Doesn't validate positive quantity or price
        this.items.push({ name, price, quantity });
    }

    getTotalPrice() {
        // BUG 2: Classical JavaScript floating point precision issue + wrong accumulator
        let total = 0;
        for (let item of this.items) {
            total += item.price * item.quantity;
        }
        return total; // e.g. 0.1 + 0.2 returns 0.30000000000000004
    }

    async applyDiscountCode(code) {
        // BUG 3: Async promise rejected or not handled
        if (code === "SAVE10") {
            return 0.10;
        } else if (code === "SAVE50") {
            return 0.50;
        }
        throw new Error("Invalid promo code");
    }
}

module.exports = ShoppingCart;
""",
    },
    "2": {
        "title": "Java - Bank Account (NullPointer & Logic Flaw)",
        "filename": "BankAccount.java",
        "lang": "java",
        "code": """// Java Bank Account with concurrency & validation bugs
public class BankAccount {
    private String owner;
    private double balance;

    public BankAccount(String owner, double initialBalance) {
        // BUG 1: No Null check on owner
        this.owner = owner;
        this.balance = initialBalance;
    }

    public void deposit(double amount) {
        // BUG 2: Allows zero or negative deposits
        this.balance += amount;
    }

    public boolean withdraw(double amount) {
        // BUG 3: Logic flaw: deducts even if overdraft occurs
        this.balance -= amount;
        if (this.balance < 0) {
            return false;
        }
        return true;
    }

    public double getBalance() {
        return this.balance;
    }
}
""",
    },
    "3": {
        "title": "C++ - Dynamic Array (Memory Leak & Out-of-Bounds)",
        "filename": "IntList.cpp",
        "lang": "cpp",
        "code": """// C++ Dynamic Integer List with common memory bugs
#include <iostream>

class IntList {
private:
    int* data;
    int capacity;
    int size;

public:
    IntList(int cap = 4) : capacity(cap), size(0) {
        data = new int[capacity];
    }

    // BUG 1: Missing destructor -> Severe Memory Leak!

    void add(int value) {
        // BUG 2: Out of bounds write when size == capacity (no resize logic)
        data[size] = value;
        size++;
    }

    int get(int index) {
        // BUG 3: No index bounds validation
        return data[index];
    }

    int getSize() const {
        return size;
    }
};
""",
    },
    "4": {
        "title": "Python - Inventory Management (Mutable Default & Index Bug)",
        "filename": "inventory.py",
        "lang": "python",
        "code": """# Python Inventory with subtle bugs
class Inventory:
    # BUG 1: Mutable default argument!
    def __init__(self, items=[]):
        self.items = items

    def add_item(self, item_name, quantity=1):
        if quantity < 0:
            return  # BUG 2: Silent failure without raising exception
        self.items.append({"name": item_name, "quantity": quantity})

    def get_first_item(self):
        # BUG 3: IndexError when inventory is empty
        return self.items[0]
""",
    },
}


# ── Mode 1: Benchmark ─────────────────────────────────────────────────────
def run_benchmark(client: LlamaCppClient):
    print(f"\n{Color.YELLOW}[*] Running Multi-Language Model Benchmark...{Color.RESET}")
    info = client.get_info()
    print(f"  • Model file:        {Color.BOLD}{info.get('model_name')}{Color.RESET}")
    print(f"  • Context window:    {info.get('context_size')} tokens")
    print(f"  • Model load time:   {info.get('load_time_seconds')} seconds")

    test_prompt = "Write a quick utility function in both Python and JavaScript that reverses words in a sentence."
    print(f"\n  • Benchmark prompt: {Color.CYAN}{test_prompt}{Color.RESET}\n")

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
    print(f"  • Speed:             {Color.GREEN}{Color.BOLD}{tps:.2f} tokens/second{Color.RESET}")
    print(f"-------------------------\n")


# ── Mode 2: Universal Interactive Coding ──────────────────────────────────
def run_interactive(client: LlamaCppClient):
    print(f"\n{Color.YELLOW}[*] Universal Interactive Assistant (Any Language / Stack){Color.RESET}")
    print("Ask to write, convert, or explain code in Python, JS, TypeScript, Java, C++, Go, etc.")
    print("Type 'exit' to return to menu.\n")

    system_prompt = (
        "You are Ojas, an advanced offline coding intelligence platform supporting all programming languages. "
        "Provide robust, elegant, production-grade code adhering to modern best practices in whatever language requested."
    )

    while True:
        try:
            user_input = input(f"{Color.BLUE}Ojas [Any Language] >> {Color.RESET}").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                break

            print(f"\n{Color.GREEN}", end="")
            for token in client.stream(
                f"<|system|>\n{system_prompt}\n<|user|>\n{user_input}\n<|assistant|>\n",
                max_tokens=650,
                temperature=0.2,
            ):
                print(token, end="", flush=True)
            print(f"{Color.RESET}\n")

        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            break


# ── Mode 3: Autonomous Dev -> Test -> Fix Loop (Python & Node.js) ─────────
def run_autonomous_loop(client: LlamaCppClient):
    print(f"\n{Color.YELLOW}[*] Autonomous Dev -> Test -> Fix Loop{Color.RESET}")
    print("Select language ecosystem:")
    print("  1. Python (Verified via Pytest)")
    print("  2. JavaScript / Node.js (Verified via Node test runner)")
    print("  3. Back to Main Menu")

    choice = input(f"\n{Color.CYAN}Select option [1-3]: {Color.RESET}").strip()

    workspace = PROJECT_ROOT / "workspace"
    workspace.mkdir(exist_ok=True)

    if choice == "1":
        # Python Calculator Loop
        from prototype_cli import run_auto_fix_loop
        run_auto_fix_loop(client)

    elif choice == "2":
        # JavaScript / Node.js Loop
        print(f"\n{Color.CYAN}[1/3] Generating JavaScript Module & Test Suite...{Color.RESET}")
        spec = (
            "Create a JavaScript module with an exported object `mathUtils` with methods:\n"
            "1. `add(a, b)`: returns a + b\n"
            "2. `divide(a, b)`: returns a / b. If b is 0, throws new Error('Division by zero')\n"
            "3. `isEven(n)`: returns true if n is even, false otherwise\n"
            "Use CommonJS `module.exports = mathUtils;`. Return ONLY valid JS code in a ```javascript ... ``` block."
        )

        resp = client.generate(
            f"<|system|>\nYou are an expert JavaScript developer.\n<|user|>\n{spec}\n<|assistant|>\n",
            max_tokens=500,
        )
        js_code = extract_code_block(resp)
        code_file = workspace / "mathUtils.js"
        code_file.write_text(js_code, encoding="utf-8")
        print(f"  Saved generated JavaScript to: {Color.BOLD}{code_file.name}{Color.RESET}")

        # Built-in Node.js test runner file
        test_content = """const test = require('node:test');
const assert = require('node:assert');
const mathUtils = require('./mathUtils.js');

test('add works correctly', () => {
    assert.strictEqual(mathUtils.add(5, 7), 12);
    assert.strictEqual(mathUtils.add(-2, 2), 0);
});

test('divide handles normal and zero division', () => {
    assert.strictEqual(mathUtils.divide(10, 2), 5);
    assert.throws(() => mathUtils.divide(10, 0), /Division by zero/);
});

test('isEven checks even and odd integers', () => {
    assert.strictEqual(mathUtils.isEven(4), true);
    assert.strictEqual(mathUtils.isEven(7), false);
});
"""
        test_file = workspace / "test_mathUtils.js"
        test_file.write_text(test_content, encoding="utf-8")

        print(f"\n{Color.CYAN}[2/3] Executing native Node.js tests (`node --test`)...{Color.RESET}")
        node_path = shutil.which("node")
        if not node_path:
            node_path = r"C:\Program Files\nodejs\node.exe"

        if os.path.exists(node_path):
            proc = subprocess.run(
                [node_path, "--test", str(test_file)],
                cwd=str(workspace),
                capture_output=True,
                text=True,
            )
            print(proc.stdout)
            if proc.returncode == 0:
                print(f"{Color.GREEN}{Color.BOLD}[✓] ALL JAVASCRIPT TESTS PASSED SUCCESSFULLY!{Color.RESET}")
            else:
                print(f"{Color.RED}[!] Tests reported failures. Reviewing error...{Color.RESET}")
                print(proc.stderr)
        else:
            print(f"{Color.YELLOW}[!] Node.js executable not found in PATH to execute live.{Color.RESET}")


# ── Mode 4: Universal Code Doctor (Any Language) ──────────────────────────
def run_universal_code_doctor(client: LlamaCppClient):
    print(f"\n{Color.YELLOW}[*] Universal Code Doctor — Inspect, Detect Bugs & Test ANY Language{Color.RESET}")
    print("Choose an option:")
    print("  1. Enter path to ANY file on your machine (.py, .js, .ts, .java, .cpp, .c, .go, .rs, etc.)")
    print("  2. Select from built-in multi-language buggy samples (JS, Java, C++, Python)")
    print("  3. Back to Main Menu")

    choice = input(f"\n{Color.CYAN}Select option [1-3]: {Color.RESET}").strip()

    code_content = ""
    file_name = "sample_code.txt"
    file_path = None

    if choice == "1":
        path_str = input(f"{Color.BLUE}Enter full or relative file path: {Color.RESET}").strip().strip('"')
        file_path = Path(path_str)
        if not file_path.exists() or not file_path.is_file():
            print(f"{Color.RED}[!] File does not exist: {path_str}{Color.RESET}")
            return
        code_content = file_path.read_text(encoding="utf-8", errors="replace")
        file_name = file_path.name
        lang_info = detect_language(file_path)

    elif choice == "2":
        print(f"\n{Color.BOLD}Select a Sample Language & Buggy Code:{Color.RESET}")
        for k, v in SAMPLES.items():
            print(f"  {k}. {v['title']}")
        sample_choice = input(f"{Color.CYAN}Choose sample [1-4]: {Color.RESET}").strip()
        sample = SAMPLES.get(sample_choice, SAMPLES["1"])

        code_content = sample["code"]
        file_name = sample["filename"]
        file_path = Path(file_name)
        lang_info = detect_language(file_path)

        print(f"\n{Color.CYAN}Selected Sample ({lang_info['name']}):{Color.RESET}")
        print(code_content)

    else:
        return

    workspace = PROJECT_ROOT / "workspace"
    workspace.mkdir(exist_ok=True)
    working_file = workspace / file_name
    working_file.write_text(code_content, encoding="utf-8")

    print(f"\n{Color.BOLD}=== Target Technology: {Color.GREEN}{lang_info['name']}{Color.RESET} ===")
    print(f"  • File:             {Color.BOLD}{file_name}{Color.RESET}")
    print(f"  • Test Framework:   {lang_info['framework']}")
    print(f"  • Code Size:        {len(code_content.splitlines())} lines")

    # Step 1: AI Code Audit
    print(f"\n{Color.CYAN}[1/3] Testing Agent auditing {lang_info['name']} for bugs, leaks & security issues...{Color.RESET}")
    audit_prompt = (
        f"<|system|>\nYou are an expert code quality auditor and senior software testing engineer specialized in {lang_info['name']}.\n"
        f"Analyze the provided code carefully. Identify every bug, logic error, memory leak, concurrency issue, "
        f"and edge case flaw. List each problem with clear headings (e.g. Bug 1: [Issue Name]), line reference, "
        f"and why it breaks.\n"
        f"<|user|>\n"
        f"CODE TO AUDIT ({lang_info['name']}):\n```{file_path.suffix.lstrip('.')}\n{code_content}\n```\n<|assistant|>\n"
    )

    print(f"\n{Color.MAGENTA}--- AI Bug Diagnostic Report ({lang_info['name']}) ---{Color.RESET}")
    audit_report = ""
    for tok in client.stream(audit_prompt, max_tokens=550, temperature=0.2):
        print(tok, end="", flush=True)
        audit_report += tok
    print(f"\n{Color.MAGENTA}-------------------------------------------------------{Color.RESET}\n")

    # Step 2: Automated Unit Test Suite Generation
    print(f"{Color.CYAN}[2/3] Generating native unit test suite using {lang_info['framework']}...{Color.RESET}")
    test_gen_prompt = (
        f"<|system|>\nYou are a professional QA engineer. Write unit tests for this {lang_info['name']} code.\n"
        f"Use the standard {lang_info['framework']} framework.\n"
        f"Test both normal execution and edge cases that trigger the bugs found above.\n"
        f"Return ONLY valid code inside a code block.\n"
        f"<|user|>\nTARGET CODE:\n```{file_path.suffix.lstrip('.')}\n{code_content}\n```\n<|assistant|>\n"
    )

    test_response = client.generate(test_gen_prompt, max_tokens=650, temperature=0.2)
    test_code = extract_code_block(test_response)

    test_file_name = f"test_{file_name}" if not file_name.startswith("test_") else f"verify_{file_name}"
    test_file = workspace / test_file_name
    test_file.write_text(test_code, encoding="utf-8")
    print(f"  Generated test suite: {Color.BOLD}{test_file.name}{Color.RESET}")

    # Optional: Real execution for Python / Node.js
    ext = file_path.suffix.lower()
    if ext == ".py":
        print(f"\n{Color.CYAN}[Execution] Running real pytest against test suite...{Color.RESET}")
        py_exe = str(PROJECT_ROOT / "runtime" / "venv" / "Scripts" / "python.exe")
        p = subprocess.run([py_exe, "-m", "pytest", str(test_file), "-v", "--tb=short"], cwd=str(workspace), capture_output=True, text=True)
        print(p.stdout)
    elif ext in (".js", ".ts"):
        node_path = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
        if os.path.exists(node_path):
            print(f"\n{Color.CYAN}[Execution] Running real Node.js test runner...{Color.RESET}")
            p = subprocess.run([node_path, "--test", str(test_file)], cwd=str(workspace), capture_output=True, text=True)
            print(p.stdout)

    # Step 3: Produce Clean, Fixed Code in that language
    print(f"\n{Color.CYAN}[3/3] Development Agent synthesizing clean, corrected {lang_info['name']} code...{Color.RESET}")
    fix_prompt = (
        f"<|system|>\nYou are a principal {lang_info['name']} architect. Provide the complete, production-ready, "
        f"fixed version of the code resolving all bugs, memory management, and edge cases.\n"
        f"Return ONLY the clean fixed code inside a single code block.\n"
        f"<|user|>\nORIGINAL CODE:\n```{file_path.suffix.lstrip('.')}\n{code_content}\n```\n\n"
        f"DIAGNOSTIC REPORT:\n{audit_report}\n<|assistant|>\n"
    )

    fixed_response = client.generate(fix_prompt, max_tokens=750, temperature=0.1)
    fixed_code = extract_code_block(fixed_response)

    stem = file_path.stem
    fixed_file = workspace / f"{stem}_fixed{file_path.suffix}"
    fixed_file.write_text(fixed_code, encoding="utf-8")

    print(f"\n{Color.GREEN}{Color.BOLD}[✓] Fixed code generated and saved successfully!{Color.RESET}")
    print(f"Saved to: {Color.CYAN}{fixed_file}{Color.RESET}\n")
    print(f"--- Preview of Fixed {lang_info['name']} Code ---")
    print(f"{Color.GREEN}{fixed_code}{Color.RESET}")
    print(f"--------------------------------------------------\n")


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

    # Check available toolchains on machine
    runtimes = []
    if os.path.exists(str(PROJECT_ROOT / "runtime" / "venv" / "Scripts" / "python.exe")):
        runtimes.append("Python 3.14")
    if shutil.which("node") or os.path.exists(r"C:\Program Files\nodejs\node.exe"):
        runtimes.append("Node.js")
    if shutil.which("javac") or os.path.exists(r"C:\Program Files\Common Files\Oracle\Java\javapath\javac.exe"):
        runtimes.append("Java")
    print(f"  • Detected Local Runtimes: {', '.join(runtimes)}")

    while True:
        print(f"\n{Color.BOLD}Select an Option:{Color.RESET}")
        print("  1. Hardware & Speed Benchmark (Tokens/sec, Latency)")
        print("  2. Universal Interactive Coding Mode (Any Language: Python, JS, Java, C++, Go...)")
        print("  3. Autonomous Dev -> Test -> Fix Loop (Python & Node.js)")
        print("  4. Universal Code Doctor: Upload/Inspect ANY File, Detect Bugs & Auto-Fix")
        print("  5. View Model & Environment Details")
        print("  6. Exit")

        choice = input(f"\n{Color.CYAN}Enter choice [1-6]: {Color.RESET}").strip()

        if choice == "1":
            run_benchmark(client)
        elif choice == "2":
            run_interactive(client)
        elif choice == "3":
            run_autonomous_loop(client)
        elif choice == "4":
            run_universal_code_doctor(client)
        elif choice == "5":
            print(f"\n{Color.BOLD}Model Details:{Color.RESET}")
            for k, v in client.get_info().items():
                print(f"  • {k}: {v}")
            settings = get_settings()
            print(f"  • Threads: {settings.n_threads}, Batch: {settings.n_batch}, Max Tokens: {settings.max_tokens}")
        elif choice == "6":
            print("\nExiting Ojas Prototype. Goodbye!")
            break
        else:
            print(f"{Color.RED}Invalid option. Please enter 1 to 6.{Color.RESET}")


if __name__ == "__main__":
    main()
