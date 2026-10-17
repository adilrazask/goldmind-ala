import tempfile
import unittest
from pathlib import Path
from ala.research import run_synthetic_experiment
from ala.memory import MemoryStore
from ala.agent import AutonomousLearningAgent

class ResearchTests(unittest.TestCase):
    def test_synthetic_experiment_is_repeatable(self):
        a = run_synthetic_experiment("test", "hypothesis", seed=123)
        b = run_synthetic_experiment("test", "hypothesis", seed=123)
        self.assertEqual(a.train_return, b.train_return)
        self.assertEqual(a.test_return, b.test_return)
        self.assertEqual(a.test_max_drawdown, b.test_max_drawdown)

    def test_agent_saves_experience(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MemoryStore(str(Path(tmp) / "memory.sqlite3"))
            agent = AutonomousLearningAgent(store)
            _, result = agent.run("test objective")
            self.assertEqual(store.experiment_count(), 1)
            self.assertEqual(store.recent_results(1)[0]["experiment_id"], result.experiment_id)

    def test_no_broker_tool_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = AutonomousLearningAgent(MemoryStore(str(Path(tmp) / "memory.sqlite3")))
            plan = agent.plan("test objective")
            self.assertNotIn("mt5", str(plan["tool_permissions"]).lower())
            self.assertNotIn("broker", str(plan["tool_permissions"]).lower())

if __name__ == "__main__":
    unittest.main()
