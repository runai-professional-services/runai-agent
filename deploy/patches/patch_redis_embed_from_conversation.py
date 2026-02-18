#!/usr/bin/env python3
"""
Patch NAT Redis plugin so items get an embedding when memory_item.memory is empty.
Without this, KNN search returns no results for items stored with only conversation (no memory text).
"""
import pathlib

REDIS_EDITOR = pathlib.Path("/app/.venv/lib/python3.13/site-packages/nat/plugins/redis/redis_editor.py")

OLD = """            # If we have memory, compute and store the embedding
            if memory_item.memory:
                logger.debug("Computing embedding for memory text")
                search_vector = await self._embedder.aembed_query(memory_item.memory)
                logger.debug("Generated embedding vector of length: %d", len(search_vector))
                memory_data["embedding"] = search_vector"""

NEW = """            # Compute embedding for vector search: use memory text or fall back to conversation content
            text_to_embed = memory_item.memory
            if not text_to_embed and memory_item.conversation:
                parts = []
                for msg in memory_item.conversation:
                    if isinstance(msg, dict) and msg.get("content"):
                        parts.append(str(msg["content"]))
                    elif getattr(msg, "content", None):
                        parts.append(str(getattr(msg, "content", "")))
                text_to_embed = " ".join(parts) if parts else ""
            if text_to_embed:
                logger.debug("Computing embedding for memory text")
                search_vector = await self._embedder.aembed_query(text_to_embed)
                logger.debug("Generated embedding vector of length: %d", len(search_vector))
                memory_data["embedding"] = search_vector"""


def main():
    text = REDIS_EDITOR.read_text()
    if OLD not in text:
        raise SystemExit("Patch target not found in redis_editor.py")
    REDIS_EDITOR.write_text(text.replace(OLD, NEW, 1))
    print("Patched redis_editor.py: embed from conversation when memory is empty")


if __name__ == "__main__":
    main()
