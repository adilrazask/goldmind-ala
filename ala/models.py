from dataclasses import dataclass, asdict
from typing import Any
import json

@dataclass
class ExperimentResult:
    experiment_id: str
    objective: str
    hypothesis: str
    strategy_name: str
    observations: int
    train_return: float
    test_return: float
    test_max_drawdown: float
    test_win_rate: float
    validation_passed: bool
    decision: str
    lesson: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
