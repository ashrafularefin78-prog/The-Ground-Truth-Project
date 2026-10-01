"""Look up page wording and resolve ``{{namespace:key}}`` tokens.

Every number that reaches the page goes through a token, and every token
resolution is recorded. tools/check.py uses that record to prove that no
figure on the site was typed by hand.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
from common import BuildError, TokenError  # noqa: E402

TOKEN_RE = re.compile(r"\{\{([a-z_]+):([a-z0-9_.]+)\}\}")
UNSAFE_RE = re.compile(r"[<>&]")
DIGIT_RE = re.compile(r"[0-9\u09e6-\u09ef]")
MISSING = object()
SAFE_NAMESPACES = {"label"}  # values that come from the content files, already text


class ContentError(BuildError):
    pass


def iter_strings(tree, prefix=""):
    """Yield (dotted key, string) for every string leaf in a content file."""
    if isinstance(tree, dict):
        for key, value in tree.items():
            if str(key).startswith("_"):
                continue
            yield from iter_strings(value, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(tree, list):
        for index, value in enumerate(tree):
            yield from iter_strings(value, f"{prefix}[{index}]")
    elif isinstance(tree, str):
        yield prefix, tree


def lookup(tree, dotted):
    node = tree
    for part in str(dotted).split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return MISSING
    return node


class Content:
    """Both language files, plus the resolver that turns tokens into values."""

    def __init__(self, root, site, stats, meta):
        self.root = Path(root)
        self.site = site or {}
        self.stats = stats or {}
        self.meta = meta or {}
        self.trees = {}
        self.resolved: list[dict] = []
        for lang in common.LANGUAGES:
            path = self.root / "src" / f"content.{lang}.json"
            tree = common.load_json(path)
            for key, value in iter_strings(tree):
                if UNSAFE_RE.search(value):
                    raise ContentError(
                        f"{path.name}: {key} contains <, > or & — write plain text and let the build escape data values"
                    )
            self.trees[lang] = tree
        status_path = self.root / "src" / "bn-status.json"
        self.bn_status = common.load_json(status_path) if status_path.exists() else {}

    # -- wording ----------------------------------------------------------
    def raw(self, lang: str, key: str):
        value = lookup(self.trees[lang], key)
        if value is MISSING:
            other = lookup(self.trees["en" if lang == "bn" else "bn"], key)
            hint = " (it exists in the other language file)" if other is not MISSING else ""
            raise ContentError(f"content.{lang}.json has no key {key}{hint}")
        if isinstance(value, (dict, list)):
            raise ContentError(f"content.{lang}.json: {key} is a group, not a line of text")
        return value

    def c(self, lang: str, key: str) -> str:
        return self.raw(lang, key)

    # -- tokens -----------------------------------------------------------
    def _namespace(self, name: str, extra: dict | None, lang: str):
        if name == "stat":
            return self.stats
        if name == "headline":
            return self.stats.get("headline", {})
        if name == "site":
            return self.site
        if name == "meta":
            return self.meta
        if name == "label":
            return self.trees[lang].get("labels", {})
        if name == "finding":
            return (extra or {}).get("finding", {})
        raise TokenError(f"unknown token namespace {{{{{name}:...}}}}")

    def t(self, lang: str, text: str, extra: dict | None = None) -> str:
        def replace(match: re.Match) -> str:
            namespace, key = match.group(1), match.group(2)
            tree = self._namespace(namespace, extra, lang)
            value = lookup(tree, key)
            if value is MISSING or value is None:
                raise TokenError(
                    f"{{{{{namespace}:{key}}}}} has no value yet. Either the data behind it is "
                    "missing, or this sentence is being rendered outside its data check."
                )
            if isinstance(value, (dict, list)):
                raise TokenError(f"{{{{{namespace}:{key}}}}} points at a group, not a single value")
            if isinstance(value, bool):
                rendered = "yes" if value else "no"
            elif isinstance(value, float):
                rendered = common.fmt_num(value)
            else:
                rendered = str(value)
            if namespace not in SAFE_NAMESPACES:
                rendered = common.esc(rendered)
            self.resolved.append({"lang": lang, "namespace": namespace, "key": key, "value": rendered})
            return rendered

        return TOKEN_RE.sub(replace, text)

    def plain(self, lang: str, text: str) -> str:
        """Text with tokens removed — used for the bare-number audit."""
        return TOKEN_RE.sub("", text)


def find_bare_numbers(tree) -> list[tuple[str, str]]:
    """Every string that contains a digit outside a token.

    A number typed straight into a sentence is a number that can drift away
    from the data, which is exactly what the assignment forbids.
    """
    offenders = []
    for key, value in iter_strings(tree):
        without_tokens = TOKEN_RE.sub("", value)
        if DIGIT_RE.search(without_tokens):
            offenders.append((key, value))
    return offenders
