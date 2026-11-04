path = r"c:\Users\SGI\Downloads\ctf-agent-orchestrator\server.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "host_bind = os.getenv" in line:
        new_lines.append('    host_bind = os.getenv("HOST", "127.0.0.1")\n')
        new_lines.append('    uvicorn.run("server:app", host=host_bind, port=port, reload=True)\n')
    else:
        new_lines.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

import ast
with open(path, "r", encoding="utf-8") as f:
    src = f.read()
ast.parse(src)
print("server.py syntax OK")
