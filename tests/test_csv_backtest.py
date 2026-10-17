import tempfile, unittest, csv
from pathlib import Path
from ala.market_data import load_ohlcv_csv
from ala.csv_backtest import run_sma_backtest

class CsvBacktestTests(unittest.TestCase):
    def make_csv(self, path):
        with path.open('w', newline='') as f:
            w=csv.writer(f); w.writerow(['timestamp','open','high','low','close','volume'])
            price=100.0
            from datetime import datetime, timedelta
            start=datetime(2024,1,1)
            for i in range(240):
                # deterministic gentle oscillating/trending price path
                price *= (1.001 if (i//30)%2==0 else 0.9995)
                w.writerow([(start+timedelta(minutes=15*i)).isoformat(),price,price*1.002,price*.998,price,100])
    def test_csv_load_and_backtest(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data.csv'; self.make_csv(p)
            rows=load_ohlcv_csv(str(p))
            report=run_sma_backtest(rows, 5, 20, 2)
            self.assertEqual(report.observations,240)
            self.assertTrue(-1 <= report.test_return < 100)
            self.assertIn(report.decision, ['KEEP_FOR_FURTHER_RESEARCH','REJECT_OR_REVISE'])
    def test_rejects_bad_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.csv'; p.write_text('time,close\n2024-01-01,100\n')
            with self.assertRaises(ValueError): load_ohlcv_csv(str(p))
if __name__=='__main__': unittest.main()
