import unittest
from pathlib import Path
from app import app, simulate

class SimulationTests(unittest.TestCase):
    def test_power_and_energy(self):
        result=simulate({'sunlight':'100','hours':'2'})
        self.assertAlmostEqual(result['power'], .03)
        self.assertAlmostEqual(result['energy'], .06)
        self.assertEqual(simulate({'sunlight':'0'})['energy'],0)
        self.assertEqual(simulate({'hours':'0'})['energy'],0)

    def test_rule_boundaries_and_priority(self):
        cases=[({'battery':'19','sunlight':'100'},'Conserve energy'),
               ({'battery':'80','sunlight':'100','trend':'falling'},'Conserve energy'),
               ({'sunlight':'29','battery':'60'},'Conserve energy'),
               ({'sunlight':'30','battery':'20'},'Charge battery'),
               ({'sunlight':'70','battery':'50'},'Run load'),
               ({'sunlight':'69','battery':'50'},'Charge battery'),
               ({'sunlight':'70','battery':'49'},'Charge battery'),
               ({'sunlight':'50','battery':'90'},'Conserve energy')]
        for args,expected in cases:
            with self.subTest(args=args): self.assertEqual(simulate(args)['action'],expected)

    def test_invalid_inputs(self):
        r=simulate({'sunlight':'nan','battery':'bad','hours':'inf','trend':'invalid'})
        self.assertEqual((r['sunlight'],r['battery'],r['hours'],r['trend']),(80,60,2,'steady'))
        r=simulate({'sunlight':'200','battery':'-1','hours':'100'})
        self.assertEqual((r['sunlight'],r['battery'],r['hours']),(100,0,24))

    def test_page_and_data_isolation(self):
        path=Path('data/measurements/solar-readings-2026-09-19.csv')
        before=path.read_bytes()
        response=app.test_client().get('/?sunlight=100&battery=10&hours=2')
        self.assertEqual(response.status_code,200)
        page=response.get_data(as_text=True)
        for expected in ['Conserve energy','0.06000 Wh','Recorded solar measurements','loaded voltage','6.73']:
            self.assertIn(expected,page)
        self.assertEqual(before,path.read_bytes())

if __name__=='__main__': unittest.main()
