"""Sandbox and Static Validator for Strategy Specifications and Declarative Implementations."""
from __future__ import annotations
import ast
import math
from typing import Dict, Any, Tuple, List
from backend.app.strategy_factory.families import ALLOWED_FAMILIES, compute_positions

BANNED_AST_CALLS = {
    "eval", "exec", "compile", "open", "__import__", "globals", "locals", 
    "getattr", "setattr", "delattr", "system", "popen", "spawn"
}
BANNED_AST_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "urllib", "requests", 
    "http", "ftplib", "builtins", "importlib", "pathlib", "ctypes"
}

class SandboxViolationError(RuntimeError):
    pass

def validate_strategy_schema(spec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    if not isinstance(spec, dict):
        return False, ["Strategy specification must be a dictionary"]
        
    family = spec.get("family")
    if not family or family not in ALLOWED_FAMILIES:
        errors.append(f"Invalid or unsupported strategy family: {family}. Allowed: {sorted(list(ALLOWED_FAMILIES))}")
        
    side = spec.get("side", "long_only")
    if side not in {"long_only", "long_short"}:
        errors.append(f"Invalid execution side: {side}")
        
    params = spec.get("parameters")
    if not isinstance(params, dict):
        errors.append("Strategy parameters must be a dictionary")
    else:
        for k, v in params.items():
            if isinstance(v, (int, float)):
                if not math.isfinite(v):
                    errors.append(f"Parameter {k} must be finite")
            elif not isinstance(v, (str, bool, list)):
                errors.append(f"Parameter {k} has invalid type: {type(v)}")

    return len(errors) == 0, errors

def static_code_analysis(code_string: str) -> Tuple[bool, List[str]]:
    """Inspects arbitrary code AST to ensure no dangerous imports, system calls, or file access."""
    if not code_string or not code_string.strip():
        return True, []
        
    errors = []
    try:
        tree = ast.parse(code_string)
    except SyntaxError as e:
        return False, [f"Syntax error in generated code: {e}"]
        
    for node in ast.walk(tree):
        # Disallow imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            errors.append("Imports are strictly forbidden in declarative strategy sandbox.")
        # Disallow dangerous builtins
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BANNED_AST_CALLS:
                errors.append(f"Forbidden function call: {node.func.id}")
            elif isinstance(node.func, ast.Attribute) and node.func.attr in BANNED_AST_CALLS:
                errors.append(f"Forbidden method call: {node.func.attr}")
        # Disallow dunder access
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            errors.append(f"Forbidden dunder attribute access: {node.attr}")
            
    return len(errors) == 0, errors

def verify_sandbox_execution(spec: Dict[str, Any]) -> Tuple[bool, str]:
    """Executes the strategy on a deterministic test dataset inside a bounded sandbox."""
    valid, errors = validate_strategy_schema(spec)
    if not valid:
        return False, f"Schema validation failed: {'; '.join(errors)}"
        
    # Generate 150 deterministic test candles
    test_candles = []
    price = 2000.0
    for i in range(150):
        price *= 1.0005 if (i // 15) % 2 == 0 else 0.9995
        test_candles.append({
            "timestamp": f"2026-01-01T{i//4:02d}:{(i%4)*15:02d}:00Z",
            "open": price,
            "high": price * 1.001,
            "low": price * 0.999,
            "close": price,
            "volume": 100.0
        })
        
    try:
        positions = compute_positions(test_candles, spec)
        if len(positions) != len(test_candles):
            return False, "Position series length mismatch"
        if any(p not in (0.0, 1.0, -1.0) for p in positions):
            return False, "Position contains values outside allowable bounds [-1.0, 1.0]"
        # Look-ahead check: first position must always be 0.0
        if positions[0] != 0.0:
            return False, "Strategy violates causality: non-zero position at bar 0"
        return True, "Sandbox verification passed"
    except Exception as e:
        return False, f"Sandbox runtime execution failed: {str(e)}"
