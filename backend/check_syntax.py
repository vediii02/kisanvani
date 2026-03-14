import ast
import os

files = ["services/voice/llm.py", "services/voice/agent_node.py"]
for file in files:
    with open(file, "r") as f:
        ast.parse(f.read(), filename=file)
print("Syntax OK")
