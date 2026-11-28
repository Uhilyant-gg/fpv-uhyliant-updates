"""A handler on a component instance must not call a window function that has the
same name as one of the component's own signals: inside the handler the bare name
resolves to the signal, so the handler re-emits itself until the JS stack overflows.
Window functions are called as ``w.name(...)`` there."""

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def signals_of(component):
    path = HERE / f"{component}.qml"
    if not path.exists():
        return set()
    return set(re.findall(r"^\s*signal\s+(\w+)\s*\(", path.read_text(encoding="utf-8"), re.M))


def window_functions(source):
    return set(re.findall(r"\bfunction\s+(\w+)\s*\(", source))


def instances(source):
    """(component name, its own text up to the matching brace) for every `Component{`."""
    for match in re.finditer(r"\b([A-Z]\w+)\s*\{", source):
        depth, start = 0, match.end() - 1
        for index in range(start, len(source)):
            if source[index] == "{":
                depth += 1
            elif source[index] == "}":
                depth -= 1
                if depth == 0:
                    yield match.group(1), source[start:index]
                    break


def test_handlers_do_not_call_shadowed_window_functions():
    problems = []
    for qml in sorted(HERE.glob("*.qml")):
        source = qml.read_text(encoding="utf-8")
        functions = window_functions(source)
        for component, body in instances(source):
            for name in signals_of(component) & functions:
                if re.search(r"(?<![\w.])" + name + r"\s*\(", body):
                    problems.append(f"{qml.name}: {component} calls {name}() — use w.{name}()")
    assert problems == []
