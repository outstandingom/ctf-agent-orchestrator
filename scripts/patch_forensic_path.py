import os

AGENT_PATH = r"c:\Users\SGI\Downloads\ctf-agent-orchestrator\agent.py"

with open(AGENT_PATH, "r", encoding="utf-8") as f:
    src = f.read()

old_block = '''def get_forensic_dir() -> str:
    r"""
    Controlled path resolver for the Forensic Engine.
    Prioritizes the exact local installation at c:\\Users\\SGI\\Downloads\\forensic
    while safely supporting environment overrides and relative fallbacks.
    """
    candidates = [
        r"c:\\Users\\SGI\\Downloads\\forensic",
        os.getenv("FORENSIC_DIR", ""),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forensic"),
        os.path.join(os.getcwd(), "forensic")
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return r"c:\\Users\\SGI\\Downloads\\forensic"'''

new_block = '''def get_forensic_dir() -> str:
    r"""
    Universal path resolver for the Forensic Engine.
    Discovers local installation across parent directories, relative workspace paths,
    environment overrides, and standard developer paths.
    """
    candidates = [
        os.getenv("FORENSIC_DIR", ""),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forensic"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "forensic"),
        os.path.join(os.getcwd(), "forensic"),
        r"c:\\Users\\SGI\\Downloads\\forensic"
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return os.path.abspath(p)
    # Default relative fallback for portable multi-user setups
    return os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forensic"))'''

assert old_block in src, "old_block not found in agent.py"
src = src.replace(old_block, new_block, 1)

with open(AGENT_PATH, "w", encoding="utf-8") as f:
    f.write(src)

import ast
try:
    ast.parse(src)
    print("✅ agent.py get_forensic_dir() updated portably")
except Exception as e:
    print(f"❌ Syntax error: {e}")
