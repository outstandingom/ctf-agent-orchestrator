"""
jailbreaks_loader.py
====================
Loader and index for the togg53192-cmd/jailbreaks submodule.

Usage (from anywhere inside ctf-agent-orchestrator):

    from jailbreaks_loader import JailbreaksLoader

    jb = JailbreaksLoader()

    # List every vendor/model
    print(jb.list_all())

    # Load a prompt by fuzzy vendor + model name
    prompt = jb.load("anthropic", "sonnet")
    print(prompt[:200])

    # List vendors
    print(jb.list_vendors())

    # List models for a vendor
    print(jb.list_models("Google"))

    # Detect prompt type
    info = jb.info("xAI", "grok-config")
    print(info)
"""

import os
import re
from pathlib import Path
from typing import Optional

# Location relative to this file (always ctf-agent-orchestrator/jailbreaks/)
_ROOT = Path(__file__).parent / "jailbreaks"


def _classify(content: str, filename: str) -> str:
    """Guess the prompt type from content heuristics."""
    fl = filename.lower()
    if "AGENTS.md" in filename or "agents" in fl:
        return "AGENTS.md workspace policy"
    if "FROM " in content and "SYSTEM " in content:
        return "Ollama Modelfile"
    if "<CFG>" in content or "<ctx>" in content:
        return "XML config block"
    if content.strip().startswith("# ") or "## " in content[:200]:
        return "System prompt (markdown)"
    if "persona" in content[:300].lower() or "you are " in content[:200].lower():
        return "Persona / identity framing"
    return "System prompt"


class JailbreaksLoader:
    """Index and loader for jailbreaks/."""

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else _ROOT
        if not self.root.exists():
            raise FileNotFoundError(
                f"jailbreaks submodule not found at {self.root}. "
                "Run: git submodule update --init --recursive"
            )
        self._index: dict[str, list[dict]] = {}
        self._build_index()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_index(self):
        for path in sorted(self.root.rglob("*.md")) + sorted(self.root.rglob("*.txt")):
            if ".git" in str(path):
                continue
            vendor = path.parent.name
            if vendor == "jailbreaks":           # files at repo root (like README)
                if path.name.lower() == "readme.md":
                    continue
                vendor = "misc"
            model  = path.stem
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
            entry = {
                "vendor":  vendor,
                "model":   model,
                "file":    str(path),
                "type":    _classify(content, path.name),
                "size":    len(content),
                "preview": content.strip()[:120].replace("\n", " "),
            }
            self._index.setdefault(vendor, []).append(entry)

    def _fuzzy_match(self, haystack: str, needle: str) -> bool:
        return needle.lower().replace("-", " ") in haystack.lower().replace("-", " ")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_vendors(self) -> list[str]:
        """Return sorted list of vendor names."""
        return sorted(self._index.keys())

    def list_models(self, vendor: str) -> list[dict]:
        """Return all model entries for a vendor (fuzzy match)."""
        for v in self._index:
            if self._fuzzy_match(v, vendor):
                return self._index[v]
        return []

    def list_all(self) -> list[dict]:
        """Return flat list of all entries."""
        out = []
        for entries in self._index.values():
            out.extend(entries)
        return out

    def find(self, vendor: str = "", model: str = "") -> list[dict]:
        """Find entries matching vendor and/or model (fuzzy)."""
        results = []
        for v, entries in self._index.items():
            if vendor and not self._fuzzy_match(v, vendor):
                continue
            for e in entries:
                if model and not self._fuzzy_match(e["model"], model):
                    continue
                results.append(e)
        return results

    def load(self, vendor: str = "", model: str = "") -> str:
        """
        Load and return prompt text for the first matching entry.
        Raises ValueError if no match found.
        """
        matches = self.find(vendor, model)
        if not matches:
            available = [(e["vendor"], e["model"]) for e in self.list_all()]
            raise ValueError(
                f"No jailbreak found for vendor={vendor!r} model={model!r}.\n"
                f"Available: {available}"
            )
        with open(matches[0]["file"], "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    def info(self, vendor: str = "", model: str = "") -> dict:
        """Return metadata dict for the first matching entry."""
        matches = self.find(vendor, model)
        if not matches:
            return {}
        return matches[0]

    def summary(self) -> str:
        """Human-readable summary of the whole collection."""
        all_entries = self.list_all()
        lines = [
            f"=== Jailbreaks Collection ({len(all_entries)} prompts, {len(self._index)} vendors) ===",
            ""
        ]
        for vendor, entries in sorted(self._index.items()):
            lines.append(f"  [{vendor}]  ({len(entries)} prompts)")
            for e in entries:
                lines.append(f"    • {e['model']:40s}  {e['type']}")
        return "\n".join(lines)
