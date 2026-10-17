import json
import os
import urllib.request


def suggest_hypothesis(objective: str, prior_lessons: list[str]) -> str | None:
    """Optional Ollama suggestion. Returns None when disabled or unavailable."""
    if os.getenv("ALA_USE_OLLAMA", "0").lower() not in {"1", "true", "yes"}:
        return None
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    prompt = ("Suggest one falsifiable hypothesis for a toy quantitative research experiment. "
              "Do not claim profitability, do not give live trading instructions, and use only synthetic data. "
              f"Objective: {objective}\nPrior lessons: {prior_lessons[-5:]}\nReturn one concise sentence.")
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    request = urllib.request.Request(f"{host}/api/generate", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = str(data.get("response", "")).strip()
        return text[:700] if text else None
    except Exception:
        return None
