#!/usr/bin/env python3
"""
Patch NAT auto_memory_agent to inject conversation content when item.memory is empty.
Otherwise only the 'memory' field is used, so stored items with conversation but empty memory
never get injected into the prompt and the LLM cannot recall them.
"""
import pathlib

AGENT_PY = pathlib.Path("/app/.venv/lib/python3.13/site-packages/nat/agent/auto_memory_wrapper/agent.py")

OLD = """        # Extract memory strings and inject as system message if available
        if memory_items:
            # Extract memory field from each MemoryItem
            memory_strings = [item.memory for item in memory_items if item.memory]
            if memory_strings:"""

NEW = """        # Extract memory strings and inject as system message if available
        if memory_items:
            # Use memory field, or fall back to conversation content (e.g. Redis items with empty memory)
            memory_strings = []
            for item in memory_items:
                if item.memory:
                    memory_strings.append(item.memory)
                elif getattr(item, "conversation", None):
                    parts = []
                    for msg in item.conversation:
                        if isinstance(msg, dict) and msg.get("content"):
                            parts.append(str(msg["content"]))
                        elif getattr(msg, "content", None):
                            parts.append(str(getattr(msg, "content", "")))
                    if parts:
                        memory_strings.append(" ".join(parts))
            if memory_strings:"""


def main():
    text = AGENT_PY.read_text()
    if OLD not in text:
        raise SystemExit("Patch target not found in auto_memory_wrapper/agent.py")
    AGENT_PY.write_text(text.replace(OLD, NEW, 1))
    print("Patched agent.py: inject conversation content when memory is empty")


if __name__ == "__main__":
    main()
