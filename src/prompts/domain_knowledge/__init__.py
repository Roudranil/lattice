import glob
import os
import re

# directory containing this file
_base_dir = os.path.dirname(__file__)
_markdown_files = glob.glob(os.path.join(_base_dir, "*.md"))
domain_knowledge = {}


def _normalize_headings(text: str) -> str:
    """
    Increase heading depth by one level.

    Rules:
    - #    -> ##
    - ##   -> ###
    - ###  -> ####
    - #### and deeper -> converted to bold text
    """

    def repl(match: re.Match) -> str:
        hashes = match.group(1)
        title = match.group(2).strip()
        level = len(hashes) + 1
        if level <= 4:
            return f"{'#' * level} {title}"
        else:
            # convert deeper headings to bold text
            return f"**{title}**"

    return re.sub(r"^(#{1,})\s+(.*)$", repl, text, flags=re.MULTILINE)


for _md_path in _markdown_files:
    with open(_md_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = _normalize_headings(content)
    key = os.path.splitext(os.path.basename(_md_path))[0]
    domain_knowledge[key] = content

__all__ = ["domain_knowledge"]
