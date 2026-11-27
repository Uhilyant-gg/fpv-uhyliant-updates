import ast
from pathlib import Path


def _tree():
    return ast.parse(Path(__file__).with_name("main.py").read_text(encoding="utf-8"))


def test_no_python_qt_message_handler_during_qml_load():
    names = {node.id for node in ast.walk(_tree()) if isinstance(node, ast.Name)}
    assert "qInstallMessageHandler" not in names


def test_qml_runtime_objects_have_process_lifetime():
    assignments = [
        node
        for node in ast.walk(_tree())
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "app"
            and target.attr == "_runtime_refs"
            for target in node.targets
        )
    ]
    assert assignments
    value = assignments[0].value
    assert isinstance(value, (ast.Tuple, ast.List))
    refs = {element.id for element in value.elts if isinstance(element, ast.Name)}
    assert {"video", "streams", "telemetry", "diag", "hardware_e2e", "fwsession"} <= refs
    # Later assignments may only extend the process-lifetime tuple, never replace it.
    for later in assignments[1:]:
        extension = later.value
        assert isinstance(extension, ast.BinOp) and isinstance(extension.op, ast.Add)
        assert isinstance(extension.left, ast.Attribute) and extension.left.attr == "_runtime_refs"
        assert isinstance(extension.left.value, ast.Name) and extension.left.value.id == "app"
        assert isinstance(extension.right, (ast.Tuple, ast.List))
