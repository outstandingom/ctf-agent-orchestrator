#!/usr/bin/env python3
"""
CTF AI Orchestrator — Interactive Setup & Ecosystem Manager
-----------------------------------------------------------
Safely installs dependencies, verifies solver libraries, checks environment variables,
and manages companion repositories without impacting existing configurations.
"""

import os
import sys
import subprocess
import shutil
import urllib.request
import json
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(BASE_DIR)

ECOSYSTEM_REPOS = [
    {
        "id": "forensic",
        "name": "Forensic Sandbox Engine",
        "url": "https://github.com/outstandingom/forensic.git",
        "target_dir": os.path.join(PARENT_DIR, "forensic"),
        "description": "LSB steganography, PK ZIP carving, and forensic file inspection engine."
    },
    {
        "id": "ctf-vector-rag",
        "name": "CTF Vector RAG Knowledge Base",
        "url": "https://github.com/outstandingom/ctf-vector-rag.git",
        "target_dir": os.path.join(PARENT_DIR, "ctf-vector-rag"),
        "description": "ZeroGPU semantic writeup retrieval and exploit pattern store."
    },
    {
        "id": "mcp-server",
        "name": "GitHub Lifetime MCP Server",
        "url": "https://github.com/outstandingom/MCP-SERVER.git",
        "target_dir": os.path.join(PARENT_DIR, "MCP-SERVER"),
        "description": "Streamable MCP server for autonomous code commits and repo operations."
    },
    {
        "id": "google-ctf",
        "name": "Google CTF Challenge Archive",
        "url": "https://github.com/google/google-ctf.git",
        "target_dir": os.path.join(PARENT_DIR, "google-ctf"),
        "description": "Official gold-standard Google CTF challenge datasets and binaries."
    },
    {
        "id": "ctfd",
        "name": "CTFd Standard Platform",
        "url": "https://github.com/CTFd/CTFd.git",
        "target_dir": os.path.join(PARENT_DIR, "CTFd"),
        "description": "Reference CTFd competition engine for local testing."
    }
]

CORE_REQUIREMENTS = [
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "openai>=1.30.0",
    "anthropic>=0.25.0",
    "pydantic>=2.7.0",
    "python-multipart>=0.0.9"
]

SOLVER_REQUIREMENTS = [
    "z3-solver>=4.12.0",
    "pycryptodome>=3.20.0",
    "sympy>=1.12",
    "randcrack>=0.1.7",
    "mpmath>=1.3.0"
]


def print_banner():
    print("\n" + "=" * 70)
    print("🛡️  CTF AI ORCHESTRATOR — ECOSYSTEM SETUP & LAUNCH WIZARD (v2.0)")
    print("=" * 70)
    print("A safe, automated manager for CTF solver tools, companion repositories,")
    print("and runtime configurations without modifying existing setup.\n")


def check_python_environment():
    print("🔍 Checking Python environment...")
    v = sys.version_info
    print(f"   Python Version: {v.major}.{v.minor}.{v.micro} ({sys.executable})")
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        print("   ⚠️  WARNING: Python 3.10+ recommended for full compatibility.")
    else:
        print("   ✅ Python version is compatible.")


def check_installed_packages():
    print("\n🔍 Checking CTF Solver Libraries...")
    libs = {
        "fastapi": "FastAPI Web Framework",
        "uvicorn": "ASGI Server",
        "z3": "Z3 Theorem Prover (SMT Solver)",
        "Crypto": "PyCryptodome (Ciphers & Hashes)",
        "sympy": "SymPy (Symbolic Mathematics & Primes)",
        "randcrack": "RandCrack (Mersenne Twister Predictor)"
    }
    missing = []
    for mod, desc in libs.items():
        try:
            __import__(mod)
            print(f"   ✅ {desc:<35} : INSTALLED")
        except ImportError:
            print(f"   ❌ {desc:<35} : MISSING")
            missing.append(mod)
    return missing


def install_dependencies():
    print("\n📦 Installing / Upgrading CTF Solver Dependencies...")
    packages = CORE_REQUIREMENTS + SOLVER_REQUIREMENTS
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + packages
    try:
        subprocess.check_call(cmd)
        print("\n✅ All dependencies successfully installed and verified!")
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")


def manage_companion_repos():
    print("\n📥 Companion Ecosystem Repositories Status:")
    print("-" * 70)
    for idx, repo in enumerate(ECOSYSTEM_REPOS, 1):
        exists = os.path.exists(repo["target_dir"])
        status = "✅ Present" if exists else "⚪ Not downloaded"
        print(f" [{idx}] {repo['name']:<32} : {status}")
        print(f"     Path: {repo['target_dir']}")
        print(f"     Info: {repo['description']}\n")

    print("[A] Download/Clone ALL missing repositories")
    print("[U] Update (git pull) all present repositories")
    print("[M] Select specific repository to download")
    print("[B] Back to Main Menu")

    choice = input("\nEnter choice [A/U/M/B] (default: B): ").strip().upper()
    if choice == "A":
        for repo in ECOSYSTEM_REPOS:
            clone_repo(repo)
    elif choice == "U":
        for repo in ECOSYSTEM_REPOS:
            update_repo(repo)
    elif choice == "M":
        num = input("Enter repository number (1-5): ").strip()
        try:
            val = int(num)
            if 1 <= val <= len(ECOSYSTEM_REPOS):
                clone_repo(ECOSYSTEM_REPOS[val - 1])
        except ValueError:
            print("Invalid selection.")


def clone_repo(repo: dict):
    target = repo["target_dir"]
    if os.path.exists(target):
        print(f"ℹ️  '{repo['name']}' already exists at {target}. Skipping clone.")
        return
    print(f"\n⏳ Cloning {repo['name']} from {repo['url']}...")
    try:
        subprocess.check_call(["git", "clone", "--depth", "1", repo["url"], target])
        print(f"✅ Successfully downloaded {repo['name']} to {target}")
    except Exception as e:
        print(f"❌ Failed to clone {repo['name']}: {e}")


def update_repo(repo: dict):
    target = repo["target_dir"]
    if not os.path.exists(target):
        print(f"⚪ '{repo['name']}' is not downloaded yet. Skipping.")
        return
    print(f"\n🔄 Updating {repo['name']}...")
    try:
        subprocess.check_call(["git", "-C", target, "pull", "origin", "main"])
        print(f"✅ {repo['name']} is up to date.")
    except Exception as e:
        print(f"⚠️  Could not update {repo['name']}: {e}")


def configure_env():
    print("\n⚙️  Interactive .env Configuration Wizard")
    print("-" * 70)
    env_file = os.path.join(BASE_DIR, ".env")
    existing = {}
    if os.path.exists(env_file):
        print(f"ℹ️  Found existing .env file at {env_file}")
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()

    print("Press ENTER to keep existing/default value.\n")
    
    current_key = existing.get("GROQ_API_KEY", "")
    masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else current_key
    new_groq = input(f"Enter GROQ_API_KEY [{masked}]: ").strip()
    if new_groq:
        existing["GROQ_API_KEY"] = new_groq

    current_port = existing.get("DASHBOARD_PORT", "8080")
    new_port = input(f"Enter DASHBOARD_PORT [{current_port}]: ").strip()
    if new_port:
        existing["DASHBOARD_PORT"] = new_port

    current_claude = existing.get("ANTHROPIC_API_KEY", "")
    masked_claude = current_claude[:8] + "..." + current_claude[-4:] if len(current_claude) > 12 else current_claude
    new_claude = input(f"Enter ANTHROPIC_API_KEY (optional) [{masked_claude}]: ").strip()
    if new_claude:
        existing["ANTHROPIC_API_KEY"] = new_claude

    # Ensure defaults
    existing.setdefault("LLM_PROVIDER", "groq")
    existing.setdefault("GROQ_MODEL", "qwen/qwen3.8-27b")
    existing.setdefault("HF_VECTOR_URL", "https://outstandingom-vector.hf.space")
    existing.setdefault("HF_KNOWLEDGE_URL", "https://outstandingom-knowledge-graph-env.hf.space")
    existing.setdefault("MCP_SERVER_URL", "https://mcp-server-2sl7.onrender.com")
    existing.setdefault("MCP_API_KEY", "")
    existing.setdefault("FORENSIC_DIR", os.path.join(PARENT_DIR, "forensic"))

    # Write safely
    with open(env_file, "w") as f:
        f.write("# CTF AI Orchestrator Configuration\n")
        for k, v in existing.items():
            f.write(f"{k}={v}\n")

    print(f"\n✅ Configuration saved safely to {env_file}")


def run_diagnostics():
    print("\n🩺 Running Complete Health & Diagnostic Suite...")
    print("-" * 70)
    port = os.getenv("DASHBOARD_PORT", "8080")
    
    # 1. Check local server
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/status")
        res = urllib.request.urlopen(req, timeout=5)
        print(f"✅ Local Server (Port {port}): ONLINE (HTTP {res.status})")
    except Exception as e:
        print(f"⚪ Local Server (Port {port}): OFFLINE ({e})")

    # 2. Check Render MCP
    try:
        req = urllib.request.Request("https://mcp-server-2sl7.onrender.com/health")
        res = urllib.request.urlopen(req, timeout=8)
        print(f"✅ Render MCP Gateway: ONLINE (HTTP {res.status})")
    except Exception as e:
        print(f"⚠️  Render MCP Gateway: Slow / Cold Start ({e})")

    # 3. Check Hugging Face Space
    try:
        req = urllib.request.Request("https://outstandingom-vector.hf.space/config")
        res = urllib.request.urlopen(req, timeout=8)
        print(f"✅ Hugging Face ZeroGPU Vector Space: ONLINE")
    except Exception as e:
        print(f"⚠️  Hugging Face Space: Slow / Cold Start ({e})")


def launch_server(port=None):
    if not port:
        port = os.getenv("DASHBOARD_PORT", "8080")
    print(f"\n🚀 Launching CTF AI Orchestrator on http://0.0.0.0:{port}...")
    print(f"👉 Access Web Command Center: http://localhost:{port}\n")
    
    # Attempt to open browser after short delay
    def open_browser():
        time.sleep(1.5)
        import webbrowser
        webbrowser.open(f"http://localhost:{port}")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    cmd = [
        sys.executable, "-m", "uvicorn", "server:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--app-dir", BASE_DIR
    ]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by operator.")


def main():
    while True:
        print_banner()
        print("[1] 🚀 Quick Launch Command Center (Default Port 8080)")
        print("[2] 📦 Install / Verify Dependencies (Z3, PyCrypto, SymPy)")
        print("[3] 📥 Download Companion Ecosystem Repositories (Forensics, MCP, CTFd)")
        print("[4] ⚙️  Configure Settings & API Keys (.env Wizard)")
        print("[5] 🩺 Run System Diagnostics & Service Matrix")
        print("[6] 🌐 Launch on Custom Port / Host")
        print("[7] ❌ Exit")
        print("-" * 70)

        choice = input("Enter option [1-7] (default: 1): ").strip()
        if not choice or choice == "1":
            check_python_environment()
            launch_server()
            break
        elif choice == "2":
            install_dependencies()
            input("\nPress ENTER to continue...")
        elif choice == "3":
            manage_companion_repos()
            input("\nPress ENTER to continue...")
        elif choice == "4":
            configure_env()
            input("\nPress ENTER to continue...")
        elif choice == "5":
            run_diagnostics()
            input("\nPress ENTER to continue...")
        elif choice == "6":
            p = input("Enter custom port (e.g. 5000, 8080, 9000): ").strip()
            if p.isdigit():
                launch_server(port=int(p))
                break
            else:
                print("Invalid port number.")
                input("\nPress ENTER to continue...")
        elif choice == "7":
            print("\n👋 Exiting. Good luck with your CTF missions!")
            break
        else:
            print("Invalid option. Please choose between 1 and 7.")
            time.sleep(1)


if __name__ == "__main__":
    main()
