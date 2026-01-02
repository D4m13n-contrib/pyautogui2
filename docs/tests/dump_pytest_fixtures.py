#!/usr/bin/env python3
import re
from pathlib import Path
from collections import defaultdict
from graphviz import Digraph

fixtures_dir = Path("./tests")

fixture_defs = {}
fixture_files = {}
fixture_autouse = set()
used_in_tests = set()

BUILTIN_FIXTURES = {
    'request', 'tmp_path', 'tmp_path_factory', 'capsys', 'capfd',
    'monkeypatch', 'mocker', 'pytestconfig', 'record_xml_attribute',
    'capfdbinary', 'capsysbinary', 'recwarn', 'pytester', 'testdir', 'self'
}

# Color palette per directory (relative to tests/fixtures/)
DIR_COLORS = {
    "common":              {"fill": "#A9DFBF", "border": "#27AE60"},
    "controller":          {"fill": "#F9E79F", "border": "#D4AC0D"},
    "core":                {"fill": "#AED6F1", "border": "#2E86C1"},
    "lib":                 {"fill": "#D5DBDB", "border": "#7F8C8D"},
    "osal":                {"fill": "#FDEBD0", "border": "#E67E22"},
    "osal/linux":          {"fill": "#FAD7A0", "border": "#E67E22"},
    "osal/macos":          {"fill": "#FADBD8", "border": "#E74C3C"},
    "osal/windows":        {"fill": "#D7BDE2", "border": "#8E44AD"},
    "utils":               {"fill": "#E8DAEF", "border": "#9B59B6"},
}
DEFAULT_COLOR = {"fill": "#EAECEE", "border": "#AAAAAA"}

FIXTURES_ROOT = "tests/fixtures/"


def get_relative_fixture_path(filepath: str) -> str:
    """Get path relative to tests/fixtures/."""
    idx = filepath.find(FIXTURES_ROOT)
    if idx >= 0:
        return filepath[idx + len(FIXTURES_ROOT):]
    return filepath


def get_dir_color(rel_path: str) -> dict:
    """Match the most specific directory prefix from relative path."""
    best = ""
    for prefix in DIR_COLORS:
        if rel_path.startswith(prefix) and len(prefix) > len(best):
            best = prefix
    return DIR_COLORS.get(best, DEFAULT_COLOR)


def find_fixtures_in_file(filepath):
    content = filepath.read_text(errors="ignore")
    pattern = re.compile(
        r'(@pytest\.fixture[^\n]*\n(?:[^\n]+\n)*?)def\s+(\w+)\s*\(([^)]*)\)',
        re.MULTILINE
    )
    for match in pattern.finditer(content):
        decorator_block = match.group(1)
        name = match.group(2)
        params_raw = match.group(3)
        params = []
        for p in params_raw.split(','):
            p = p.strip().split(':')[0].split('=')[0].strip()
            if p and p not in BUILTIN_FIXTURES and not p.startswith('*'):
                params.append(p)
        if name not in fixture_defs:
            fixture_defs[name] = params
            fixture_files[name] = str(filepath.relative_to(Path(".")))
            if re.search(r'autouse\s*=\s*True', decorator_block):
                fixture_autouse.add(name)


def find_used_in_tests_in_file(filepath):
    content = filepath.read_text(errors="ignore")
    pattern = re.compile(r'def\s+(test_\w+)\s*\(([^)]*)\)', re.MULTILINE)
    for match in pattern.finditer(content):
        params_raw = match.group(2)
        for p in params_raw.split(','):
            p = p.strip().split(':')[0].split('=')[0].strip()
            if p and p not in BUILTIN_FIXTURES and not p.startswith('*'):
                used_in_tests.add(p)


# Scan
if fixtures_dir.exists():
    for f in fixtures_dir.rglob("*.py"):
        find_fixtures_in_file(f)
        find_used_in_tests_in_file(f)

# Build nested directory tree
# Group fixtures by their relative path (relative to tests/fixtures/)
# Structure: {dir_parts_tuple: {filename: [fixture_names]}}
file_fixtures = defaultdict(list)  # rel_filepath -> [fixture_names]
for name, fpath in fixture_files.items():
    rel = get_relative_fixture_path(fpath)
    file_fixtures[rel].append(name)


def build_dir_tree(file_fixtures):
    """Build a nested dict representing the directory structure.

    Returns a tree like:
    {
        "__files__": {"manager.py": ["controller_manager"]},
        "decorators": {
            "__files__": {"failsafe.py": ["failsafe_manager_mocked", ...]},
        }
    }
    """
    tree = {}
    for rel_path, fixtures in file_fixtures.items():
        parts = Path(rel_path).parts  # e.g. ("utils", "decorators", "failsafe.py")
        node = tree
        # Navigate/create directories
        for dir_part in parts[:-1]:
            if dir_part not in node:
                node[dir_part] = {}
            node = node[dir_part]
        # Add file
        filename = parts[-1]
        if "__files__" not in node:
            node["__files__"] = {}
        node["__files__"][filename] = fixtures
    return tree


dir_tree = build_dir_tree(file_fixtures)

# Graph
dot = Digraph(comment="Pytest Fixtures Dependencies", format='svg')
dot.attr(rankdir='LR', fontname='Helvetica', fontsize='10', splines='ortho',
         bgcolor='#FAFAFA', pad='0.5', nodesep='0.4', ranksep='1.2')
dot.attr('node', fontname='Helvetica', fontsize='10', style='filled',
         shape='box', margin='0.15,0.08')
dot.attr('edge', fontname='Helvetica', fontsize='9')

# Track all known fixture names for orphan/unknown detection
all_deps = set()
for deps in fixture_defs.values():
    all_deps.update(deps)

cluster_counter = [0]


def make_cluster_id():
    cluster_counter[0] += 1
    return f"cluster_{cluster_counter[0]}"


def render_tree(parent_graph, tree, dir_path_parts=()):
    """Recursively render the directory tree as nested clusters."""
    # Render files at this level
    if "__files__" in tree:
        for filename, fixtures in sorted(tree["__files__"].items()):
            file_cluster_id = make_cluster_id()
            with parent_graph.subgraph(name=file_cluster_id) as file_sub:
                file_sub.attr(
                    label=f"{filename}",
                    style='rounded,filled', fillcolor='#F8F9F9',
                    color='#CCCCCC', fontsize='9', fontname='Helvetica'
                )
                for fname in sorted(fixtures):
                    rel = get_relative_fixture_path(fixture_files.get(fname, ""))
                    colors = get_dir_color(rel)
                    node_style = 'filled'
                    node_color = colors["border"]
                    penwidth = '1'

                    if fname in fixture_autouse:
                        node_style = 'filled,bold'
                        node_color = '#FC392B'
                        penwidth = '2.5'
                    elif fname not in used_in_tests and fname not in all_deps:
                        node_style = 'filled,bold'
                        node_color = '#E74C3C'
                        penwidth = '2'

                    label = f"!! {fname} !!" if fname in fixture_autouse else fname
                    if fname not in used_in_tests and fname not in all_deps and fname not in fixture_autouse:
                        label = f"-- {fname} --"

                    file_sub.node(
                        fname, label,
                        fillcolor=colors["fill"], color=node_color,
                        style=node_style, penwidth=penwidth
                    )

    # Render subdirectories
    for key in sorted(tree.keys()):
        if key == "__files__":
            continue
        subtree = tree[key]
        sub_path_parts = dir_path_parts + (key,)
        dir_rel = "/".join(sub_path_parts)
        colors = get_dir_color(dir_rel)
        dir_cluster_id = make_cluster_id()

        with parent_graph.subgraph(name=dir_cluster_id) as dir_sub:
            dir_sub.attr(
                label=f"{key}",
                style='rounded,bold', color=colors["border"],
                bgcolor=colors["fill"] + "33",  # very light tint
                fontsize='11', fontname='Helvetica Bold',
                penwidth='2'
            )
            render_tree(dir_sub, subtree, sub_path_parts)


render_tree(dot, dir_tree)

# Unknown/external fixtures (deps not defined in our tree)
for fname, deps in sorted(fixture_defs.items()):
    for dep in deps:
        if dep not in fixture_defs:
            dot.node(dep, f"?? {dep} ??", style='filled,dashed', fillcolor='#EAECEE',
                     shape='box', margin='0.15,0.08', color='#999999', fontcolor='#999999')

# Edges
for fname, deps in sorted(fixture_defs.items()):
    for dep in deps:
        if dep in fixture_files:
            rel = get_relative_fixture_path(fixture_files[dep])
            color = get_dir_color(rel)["border"] + "99"
        else:
            color = "#999999"
        dot.edge(dep, fname, color=color)

# Terminal nodes
if fixture_autouse:
    dot.node('__autouse__', 'All tests (autouse)',
             shape='doublecircle', style='filled', fillcolor='#F5B7B1',
             fontsize='11', fontname='Helvetica Bold', color='#C0392B')
    for fname in sorted(fixture_autouse):
        dot.edge(fname, '__autouse__', style='dashed', color='#C0392B')

dot.node('__used__', '✔ Used in tests',
         shape='doublecircle', style='filled', fillcolor='#82E0AA',
         fontsize='11', fontname='Helvetica Bold', color='#27AE60')
for fname in sorted(set(fixture_defs.keys()) & used_in_tests):
    dot.edge(fname, '__used__', style='dashed', color='#27AE60')

# Legend
with dot.subgraph(name='cluster_legend') as leg:
    leg.attr(label='Legend', style='rounded', color='#AAAAAA',
             fontsize='10', fontname='Helvetica Bold')
    for i, (dirname, colors) in enumerate(sorted(DIR_COLORS.items())):
        leg.node(f'leg_{i}', f"{dirname}", style='filled',
                 fillcolor=colors["fill"], shape='box', fontsize='9',
                 color=colors["border"])
    leg.node('leg_unknown', '?? unknown ??', style='filled,dashed',
             fillcolor='#EAECEE', shape='box', fontsize='9',
             color='#999999', fontcolor='#999999')
    leg.node('leg_orphan', '-- orphan --', style='filled,bold',
             fillcolor='#FADBD8', shape='box', fontsize='9', color='#E74C3C')
    leg.node('leg_autouse', '!! autouse !!', style='filled,bold',
             fillcolor='#F5B7B1', shape='box', fontsize='9', color='#FC392B')

# Render
output_path = Path("./docs/tests/pytest_fixture_graph")
dot.save(str(output_path.with_suffix(".dot")))
dot.render(str(output_path), cleanup=True)
print(f"Graph saved to {output_path}.svg")

###############
# Debug
###############
#print(f"Found {len(fixture_defs)} fixtures ({len(fixture_autouse)} autouse)")
#for name, deps in sorted(fixture_defs.items()):
#    auto_tag = " [AUTOUSE]" if name in fixture_autouse else ""
#    print(f"  {name} <- {deps} [{fixture_files.get(name, '?')}]{auto_tag}")
#
