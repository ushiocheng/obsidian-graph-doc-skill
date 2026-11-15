#!/usr/bin/env python3
"""Validate an obsidian-graph-doc vault. Standard library only.

Usage: python3 validate.py [VAULT_DIR]      (default: docs)
Exit code: 0 = no errors (warnings allowed), 1 = errors, 2 = bad usage.

A "vault note" is a Markdown file whose frontmatter has a `type` key. Other
Markdown files in the vault are left alone but count as link targets.
"""
import glob
import os
import re
import subprocess
import sys

TYPES = {"index", "overview", "module", "interface", "data-model", "flow",
         "external", "concept", "decision"}
LINK_KEYS = ("part_of", "depends_on", "implements", "about", "supersedes", "see_also")
NEEDS_SOURCES = {"module", "interface", "data-model", "flow"}
WIKILINK = re.compile(r"\[\[([^\]|#]*)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
FENCE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.S | re.M)
INLINE_CODE = re.compile(r"`[^`\n]*`")
KEY_LINE = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")
ITEM_LINE = re.compile(r"^\s+-\s+(.*)$|^-\s+(.*)$")
INLINE_ITEM = re.compile(r'"[^"]*"|\'[^\']*\'|[^,\s][^,]*')


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def split_frontmatter(text):
    """Return (frontmatter, body), with frontmatter None if absent."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    return text[4:end], text[end + 4:]


def parse_frontmatter(raw):
    """Parse the flat YAML subset this format allows: scalars and lists."""
    data, key = {}, None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = ITEM_LINE.match(line)
        if item and key is not None:
            if not isinstance(data[key], list):
                data[key] = []
            data[key].append(unquote(item.group(1) or item.group(2) or ""))
            continue
        match = KEY_LINE.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if value.startswith("[") and value.endswith("]") and not value.startswith("[["):
            data[key] = [unquote(v) for v in INLINE_ITEM.findall(value[1:-1])]
        else:
            data[key] = unquote(value)
    return data


def as_list(value):
    if isinstance(value, list):
        return value
    return [value] if value else []


def link_targets(text):
    return [t.strip() for t in WIKILINK.findall(text) if t.strip()]


def main(argv):
    if len(argv) > 2:
        print(__doc__, file=sys.stderr)
        return 2
    vault = os.path.abspath(argv[1] if len(argv) == 2 else "docs")
    if not os.path.isdir(vault):
        print("not a directory: " + vault, file=sys.stderr)
        return 2

    top = subprocess.run(["git", "-C", vault, "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    in_git = top.returncode == 0
    root = top.stdout.strip() if in_git else os.path.dirname(vault)

    errors, warnings = [], []
    by_name, by_path, other_files, notes = {}, {}, set(), {}

    for folder, dirs, files in os.walk(vault):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in sorted(files):
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, vault).replace(os.sep, "/")
            if not name.lower().endswith(".md"):
                other_files.add(name.lower())
                other_files.add(rel.lower())
                continue
            by_name.setdefault(name[:-3].lower(), []).append(rel)
            by_path[rel[:-3].lower()] = rel
            with open(path, encoding="utf-8") as handle:
                raw, body = split_frontmatter(handle.read())
            if raw is None:
                continue
            meta = parse_frontmatter(raw)
            if "type" in meta:
                notes[rel] = (meta, raw, body)

    for name, paths in sorted(by_name.items()):
        if len(paths) > 1:
            errors.append("duplicate note name '%s': %s" % (name, ", ".join(paths)))

    def resolve(target):
        target = target.lower()
        if target.endswith(".md"):
            target = target[:-3]
        if "/" in target:
            hits = [p for p in by_path if p == target or p.endswith("/" + target)]
            return by_path[hits[0]] if hits else None
        if target in by_name:
            return by_name[target][0]
        return target if target in other_files else None

    inbound = {rel: 0 for rel in notes}

    for rel, (meta, raw, body) in sorted(notes.items()):
        def err(message, rel=rel):
            errors.append("%s: %s" % (rel, message))

        kind = meta.get("type")
        if kind not in TYPES:
            err("unknown type '%s'" % kind)
        for key in ("title", "description"):
            if not meta.get(key):
                err("missing '%s'" % key)
        for line in raw.splitlines():
            if "[[" in line and '"[[' not in line and "'[[" not in line:
                err("frontmatter wikilink must be quoted: " + line.strip())

        prose = INLINE_CODE.sub("", FENCE.sub("", body))
        body_links = link_targets(prose)
        front_links = []
        for key in LINK_KEYS:
            for value in as_list(meta.get(key)):
                found = link_targets(value)
                if not found:
                    err("%s entry is not a wikilink: %s" % (key, value))
                front_links.extend((key, t) for t in found)
        for key, value in meta.items():
            if key not in LINK_KEYS and "[[" in str(value):
                err("wikilink under unknown link key '%s'" % key)
        if len(as_list(meta.get("part_of"))) > 1:
            err("part_of has more than one parent")

        body_resolved = set()
        for target in body_links:
            hit = resolve(target)
            if hit is None:
                err("broken link [[%s]]" % target)
            else:
                body_resolved.add(hit)
        front_resolved = set()
        for key, target in front_links:
            hit = resolve(target)
            if hit is None:
                err("broken link in %s: [[%s]]" % (key, target))
                continue
            front_resolved.add(hit)
            if hit not in body_resolved:
                err("%s [[%s]] does not also appear in the body" % (key, target))
            if hit == rel:
                err("%s links to itself" % key)
        for hit in body_resolved | front_resolved:
            if hit in inbound and hit != rel:
                inbound[hit] += 1

        sources = as_list(meta.get("sources"))
        if kind in NEEDS_SOURCES and not sources:
            err("type '%s' needs 'sources'" % kind)
        for source in sources:
            if not glob.glob(os.path.join(root, source), recursive=True):
                err("sources path matches nothing: " + source)
        commit = str(meta.get("verified_commit") or "")
        if sources and not commit:
            err("missing 'verified_commit'")
        elif commit == "uncommitted":
            warnings.append("%s: verified_commit is 'uncommitted'" % rel)
        elif sources and in_git:
            specs = [":(glob)" + s if any(c in s for c in "*?[") else s for s in sources]
            diff = subprocess.run(
                ["git", "-C", root, "diff", "--name-only", commit, "--"] + specs,
                capture_output=True, text=True)
            if diff.returncode != 0:
                err("verified_commit '%s' is not a known commit" % commit)
            elif diff.stdout.strip():
                changed = diff.stdout.split()
                warnings.append("%s: stale, changed since %s: %s"
                                % (rel, commit, ", ".join(changed)))

    kinds = [meta.get("type") for meta, _, _ in notes.values()]
    for single in ("index", "overview"):
        if notes and kinds.count(single) != 1:
            errors.append("expected exactly one '%s' note, found %d"
                          % (single, kinds.count(single)))
    for rel, count in sorted(inbound.items()):
        if count == 0 and notes[rel][0].get("type") != "index":
            warnings.append("%s: orphan, no note links to it" % rel)

    for message in errors:
        print("ERROR  " + message)
    for message in warnings:
        print("WARN   " + message)
    print("%d notes, %d errors, %d warnings" % (len(notes), len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
