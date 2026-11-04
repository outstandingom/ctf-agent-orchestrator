"""Fix stray brace in OPENAI_TOOLS inserted by patch script."""
import re

AGENT_PATH = r"c:\Users\SGI\Downloads\ctf-agent-orchestrator\agent.py"

with open(AGENT_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the problem: there is a bare `    }` line immediately followed by `    },`
# This happens at the junction between the original list end and the new tool entries
# Pattern: line N = "    }\r\n", line N+1 = "    },\r\n"
fixed = []
i = 0
found = False
while i < len(lines):
    line = lines[i]
    # Look for: "    }\n" or "    }\r\n" followed immediately by "    },\n" or "    },\r\n"
    next_line = lines[i+1] if i+1 < len(lines) else ""
    if (line.rstrip("\r\n") == "    }") and (next_line.rstrip("\r\n") == "    },") and not found:
        # Merge: drop the bare `    }` line, keep only `    },`
        # But we need to check: this should be AFTER the last original tool block
        # Verify by checking context (the line before should be `        }`)
        prev_line = lines[i-1].rstrip("\r\n") if i > 0 else ""
        if prev_line == "        }":
            print(f"[FOUND] Stray brace at line {i+1}, merging with next line")
            # Skip this line (the stray bare `}`)
            found = True
            i += 1
            continue
    fixed.append(line)
    i += 1

if found:
    with open(AGENT_PATH, "w", encoding="utf-8") as f:
        f.writelines(fixed)
    print("Stray brace removed. Verifying syntax...")
    import ast
    with open(AGENT_PATH, "r", encoding="utf-8") as f:
        src = f.read()
    try:
        ast.parse(src)
        print("✅ Syntax OK")
    except SyntaxError as e:
        print(f"❌ Still has syntax error at line {e.lineno}: {e.msg}")
        # Print context
        for idx, ln in enumerate(src.splitlines()[max(0,e.lineno-4):e.lineno+2], start=max(0,e.lineno-4)+1):
            print(f"  {idx:4d}: {ln}")
else:
    print("Pattern not found. Printing lines 629-640 for diagnosis:")
    for i, ln in enumerate(lines[628:640], start=629):
        print(f"  {i}: {repr(ln)}")
