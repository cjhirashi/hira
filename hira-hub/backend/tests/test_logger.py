"""`core/logger.py::get_logger` — observabilidad JSON estructurada.

Cubre RF-004 (`spec.md`): cada log es JSON válido con `timestamp, level,
service, module, trace_id, message`. Cero `print()` en el módulo.
"""
import inspect
import json


def test_get_logger_emits_structured_json(capsys):
    from core.logger import get_logger

    logger = get_logger("test_module")
    logger.info("hola mundo")

    captured = capsys.readouterr()
    lines = [line for line in captured.out.strip().splitlines() if line]
    assert len(lines) == 1

    record = json.loads(lines[0])
    assert set(record.keys()) >= {
        "timestamp",
        "level",
        "service",
        "module",
        "trace_id",
        "message",
    }
    assert record["level"] == "INFO"
    assert record["service"] == "hira-hub"
    assert record["module"] == "test_module"
    assert record["message"] == "hola mundo"


def test_get_logger_defaults_trace_id_when_no_context(capsys):
    from core.logger import get_logger

    logger = get_logger("test_module_default")
    logger.info("sin trace")

    captured = capsys.readouterr()
    record = json.loads(captured.out.strip().splitlines()[-1])
    assert record["trace_id"] == "-"


def test_get_logger_includes_trace_id_from_context(capsys):
    from core.logger import get_logger, trace_id_var

    logger = get_logger("test_module_ctx")
    token = trace_id_var.set("abc-123")
    try:
        logger.info("con trace")
    finally:
        trace_id_var.reset(token)

    captured = capsys.readouterr()
    record = json.loads(captured.out.strip().splitlines()[-1])
    assert record["trace_id"] == "abc-123"


def test_no_print_used_in_logger_module():
    from core import logger as logger_module

    source = inspect.getsource(logger_module)
    assert "print(" not in source
