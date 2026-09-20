"""
graft_engine.py - Reusable Native Python Graft Knowledge Graph Generator
Can be run on ANY repository path to generate a complete graft/ directory.
Usage: python graft_engine.py [target_directory]
"""
import os
import sys
import ast
import json
import time
from collections import defaultdict
from typing import Dict, List, Any, Set

# Windows UTF-8 stdout configuration
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def parse_python_module(filepath: str, root_dir: str) -> Dict[str, Any]:
    rel_path = os.path.relpath(filepath, root_dir).replace("\\", "/")
    filename = os.path.basename(filepath)
    mod_name = os.path.splitext(filename)[0]

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    try:
        tree = ast.parse(content, filename=filepath)
    except Exception as e:
        return {
            "name": mod_name,
            "filename": filename,
            "rel_path": rel_path,
            "summary": f"Parsing error: {e}",
            "classes": [],
            "functions": [],
            "raw_imports": [],
            "internal_deps": [],
            "lines": len(content.splitlines()),
            "bytes": len(content)
        }

    docstring = ast.get_docstring(tree) or ""
    summary = docstring.strip().split("\n\n")[0].replace("\n", " ") if docstring else "No module docstring."

    classes = []
    functions = []
    imports = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes.append({
                "name": node.name,
                "methods": methods[:15],
                "doc": ast.get_docstring(node) or ""
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            functions.append({
                "name": node.name,
                "args": args,
                "is_async": isinstance(node, ast.AsyncFunctionDef)
            })
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    # Dynamic imports inside functions
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return {
        "name": mod_name,
        "filename": filename,
        "rel_path": rel_path,
        "summary": summary,
        "classes": classes,
        "functions": functions,
        "raw_imports": list(set(imports)),
        "lines": len(content.splitlines()),
        "bytes": len(content)
    }

def build_graft(target_dir: str = "."):
    root_dir = os.path.abspath(target_dir)
    graft_dir = os.path.join(root_dir, "graft")
    os.makedirs(graft_dir, exist_ok=True)

    print(f"🚀 [Graft Engine] Scanning repository: {root_dir}")

    py_files = []
    ignore_dirs = {".git", ".venv", "venv", "env", "__pycache__", "node_modules", "dist", "build"}
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))

    all_mod_names = {os.path.splitext(os.path.basename(p))[0] for p in py_files}
    modules: Dict[str, Dict[str, Any]] = {}

    for p in py_files:
        info = parse_python_module(p, root_dir)
        info["internal_deps"] = sorted(list(set(info["raw_imports"]).intersection(all_mod_names) - {info["name"]}))
        modules[info["name"]] = info

    inbound_deps = defaultdict(list)
    for mod_name, info in modules.items():
        for dep in info["internal_deps"]:
            inbound_deps[dep].append(mod_name)

    for mod_name in modules:
        modules[mod_name]["inbound_deps"] = sorted(inbound_deps[mod_name])

    print(f"✅ [Graft Engine] Discovered {len(modules)} Python modules.")

    # 1. Overview
    hubs = sorted(modules.values(), key=lambda m: len(m["inbound_deps"]), reverse=True)[:10]
    proj_name = os.path.basename(root_dir)

    overview_content = f"""# {proj_name} — Architectural Overview (Graft Knowledge Graph)

> **Context Layer for AI Coding Agents**: Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}.

---

## 1. System Summary & Metrics
- **Root Directory**: `{root_dir}`
- **Total Python Modules**: {len(modules)}
- **Total In-Repo Dependency Edges**: {sum(len(m['internal_deps']) for m in modules.values())}

---

## 2. Central Hub Modules (Most Imported)

| Module | Purpose | Inbound Importers | Outbound Dependencies |
| :--- | :--- | :--- | :--- |
"""
    for h in hubs:
        overview_content += f"| [`{h['filename']}`](file:///{h['rel_path']}) | {h['summary'][:75]}... | **{len(h['inbound_deps'])} modules** | {len(h['internal_deps'])} modules |\n"

    with open(os.path.join(graft_dir, "overview.md"), "w", encoding="utf-8") as f:
        f.write(overview_content)

    # 2. Modules Graph
    mg_content = f"""# {proj_name} — Module Dependency & Function Catalog (Graft)

This catalog enumerates all **{len(modules)} modules**, their exported functions, classes, and internal dependency links.

---

"""
    for name in sorted(modules.keys()):
        m = modules[name]
        mg_content += f"## `{m['filename']}`\n"
        mg_content += f"- **File Path**: [`{m['rel_path']}`](file:///{m['rel_path']})\n"
        mg_content += f"- **Summary**: {m['summary']}\n"
        mg_content += f"- **Lines**: {m['lines']} | **Size**: {m['bytes']:,} bytes\n"

        if m["internal_deps"]:
            deps_str = ", ".join([f"`{d}.py`" for d in m["internal_deps"]])
            mg_content += f"- **Imports (Outbound)**: {deps_str}\n"
        else:
            mg_content += f"- **Imports (Outbound)**: *None (Leaf Module)*\n"

        if m["inbound_deps"]:
            in_str = ", ".join([f"`{d}.py`" for d in m["inbound_deps"]])
            mg_content += f"- **Imported By (Inbound)**: {in_str}\n"
        else:
            mg_content += f"- **Imported By (Inbound)**: *Top-Level / Entry Script*\n"

        if m["classes"]:
            mg_content += f"- **Classes**:\n"
            for c in m["classes"]:
                methods_str = f" (Methods: {', '.join(c['methods'])})" if c["methods"] else ""
                mg_content += f"  - `class {c['name']}`{methods_str}\n"

        if m["functions"]:
            funcs_sample = m["functions"][:12]
            funcs_str = ", ".join([f"`{fn['name']}()`" for fn in funcs_sample])
            more_str = f" *(+ {len(m['functions']) - 12} more)*" if len(m["functions"]) > 12 else ""
            mg_content += f"- **Functions ({len(m['functions'])})**: {funcs_str}{more_str}\n"

        mg_content += "\n---\n\n"

    with open(os.path.join(graft_dir, "modules_graph.md"), "w", encoding="utf-8") as f:
        f.write(mg_content)

    # 3. JSON Graph
    nodes = []
    edges = []
    for name, m in modules.items():
        nodes.append({
            "id": name,
            "filename": m["filename"],
            "path": m["rel_path"],
            "summary": m["summary"],
            "lines": m["lines"]
        })
        for dep in m["internal_deps"]:
            edges.append({
                "source": name,
                "target": dep,
                "type": "imports"
            })

    with open(os.path.join(graft_dir, "architecture_graph.json"), "w", encoding="utf-8") as f:
        json.dump({
            "generator": "Native Python Graft Engine",
            "project_name": proj_name,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "nodes": nodes,
            "edges": edges
        }, f, indent=2)

    print(f"🎉 [Graft Engine] Successfully written to: {graft_dir}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    build_graft(target)
