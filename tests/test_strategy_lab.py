import tempfile, unittest
from pathlib import Path
from datetime import datetime, timedelta
from ala.strategy_lab import generate_candidates, evaluate_candidate
from ala.learning import choose_next_candidate, record_experience
from ala.memory import MemoryStore

class StrategyLabTests(unittest.TestCase):
    def candles(self, n=260):
        rows=[]; price=2000.0; start=datetime(2024,1,1)
        for i in range(n):
            # deterministic oscillating trend fixture
            price *= 1.0008 if (i//35)%2==0 else 0.9993
            rows.append({"timestamp":(start+timedelta(minutes=15*i)).isoformat(),"open":price,"high":price*1.002,"low":price*.998,"close":price,"volume":100.0})
        return rows
    def test_generates_multiple_allowlisted_families(self):
        candidates=generate_candidates()
        self.assertGreater(len(candidates),30)
        self.assertEqual({c['family'] for c in candidates},{'sma_crossover','momentum','breakout','rsi_mean_reversion'})
    def test_evaluates_candidate_and_rejects_unknown_family(self):
        report=evaluate_candidate(self.candles(),{"family":"sma_crossover","fast":5,"slow":20,"side":"long_only"})
        self.assertIn(report.decision,{'CANDIDATE_FOR_FURTHER_VALIDATION','REJECT_OR_REVISE'})
        with self.assertRaises(ValueError): evaluate_candidate(self.candles(),{"family":"execute_python","code":"danger"})
    def test_experience_changes_next_candidate_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory=MemoryStore(str(Path(tmp)/'m.sqlite3'))
            first=choose_next_candidate(memory)
            report=evaluate_candidate(self.candles(),first)
            record_experience(memory,report)
            second=choose_next_candidate(memory)
            self.assertNotEqual(first,second)
            self.assertEqual(len(memory.candidate_history()),1)

if __name__=='__main__': unittest.main()
