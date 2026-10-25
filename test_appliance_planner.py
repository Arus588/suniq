import unittest
from appliance_planner import demo_forecast, plan_appliance

class PlannerTests(unittest.TestCase):
    def test_energy_balance_and_deadline(self):
        p=plan_appliance(demo_forecast(),1.2,2,8,18)
        self.assertGreaterEqual(p['start'],8)
        self.assertLessEqual(p['end'],18)
        self.assertAlmostEqual(p['energy_kwh'],2.4)
        self.assertAlmostEqual(p['solar_kwh']+p['grid_kwh'],2.4)
        self.assertLessEqual(p['grid_kwh'],p['baseline']['grid_kwh'])
        self.assertAlmostEqual(p['grid_kwh'],min(c['grid_kwh'] for c in p['candidates']))

    def test_no_solar_all_grid_and_tie_earliest(self):
        rows=[dict(hour=i*.5,solar_kw=0,home_kw=1) for i in range(48)]
        p=plan_appliance(rows,2,1,8,18)
        self.assertEqual(p['grid_kwh'],2)
        self.assertEqual(p['start'],8)

    def test_existing_home_load_reserves_solar(self):
        rows=[dict(hour=i*.5,solar_kw=2,home_kw=1.5) for i in range(48)]
        p=plan_appliance(rows,1,1,8,9)
        self.assertAlmostEqual(p['solar_kwh'],.5)
        self.assertAlmostEqual(p['grid_kwh'],.5)

    def test_impossible_or_invalid_tasks(self):
        for args in [(1,3,17,18),(float('nan'),1,8,18),(1,1,19,18),(1,.7,8,18)]:
            with self.assertRaises(ValueError):plan_appliance(demo_forecast(),*args)

    def test_full_forecast_required(self):
        with self.assertRaises(ValueError):plan_appliance(demo_forecast()[:20],1,1,8,18)

    def test_full_solar_covers_task(self):
        rows=[dict(hour=i*.5,solar_kw=4,home_kw=1) for i in range(48)]
        p=plan_appliance(rows,2,2,8,18)
        self.assertEqual(p['grid_kwh'],0)
        self.assertEqual(p['solar_percent'],100)


class PlannerPageTests(unittest.TestCase):
    def setUp(self):
        from app import app
        self.client=app.test_client()

    def test_planner_result_and_invalid_window(self):
        page=self.client.get('/planner').get_data(as_text=True)
        self.assertIn('Recommended start',page)
        self.assertIn('Illustrative forecast',page)
        self.assertNotIn('Explore a scenario',page)
        response=self.client.get('/planner?duration=3&earliest=17&deadline=18')
        self.assertEqual(response.status_code,200)
        self.assertIn('cannot finish',response.get_data(as_text=True))
        self.assertNotIn('Recommended start',response.get_data(as_text=True))

    def test_save_plan_and_csrf(self):
        self.client.get('/planner?appliance=ev&earliest=9&deadline=19&duration=3&power=3.6')
        with self.client.session_transaction() as state:
            csrf=state['csrf']
            self.assertEqual(state['latest_appliance_plan']['appliance'],'EV charging')
        self.assertEqual(self.client.post('/planner').status_code,400)
        page=self.client.post('/planner',data={'csrf_token':csrf},follow_redirects=True).get_data(as_text=True)
        self.assertIn('Saved plan',page)
        self.assertIn('EV charging',page)
        with self.client.session_transaction() as state:
            self.assertEqual(state['saved_appliance_plan']['appliance'],'EV charging')

class DayPlannerTests(unittest.TestCase):
    def task(self,key='a',power=1,duration=1,earliest=10,deadline=12):
        return dict(id=key,name=key,power_kw=power,duration_hours=duration,earliest=earliest,deadline=deadline)

    def test_parallel_solar_is_not_double_counted(self):
        from appliance_planner import plan_day
        forecast=[dict(hour=i*.5,solar_kw=1,home_kw=0) for i in range(48)]
        p=plan_day(forecast,[self.task('a',earliest=10,deadline=11),self.task('b',earliest=10,deadline=11)])
        self.assertTrue(p['has_overlap'])
        self.assertAlmostEqual(p['solar_kwh'],1)
        self.assertAlmostEqual(p['grid_kwh'],1)
        self.assertAlmostEqual(p['energy_kwh'],2)

    def test_serial_preference_and_deadlines(self):
        from appliance_planner import plan_day
        p=plan_day(demo_forecast(),[self.task('a'),self.task('b')],False)
        self.assertFalse(p['has_overlap'])
        for r in p['rows']:
            self.assertGreaterEqual(r['start'],r['earliest'])
            self.assertLessEqual(r['end'],r['deadline'])
        self.assertAlmostEqual(p['solar_kwh']+p['grid_kwh'],p['energy_kwh'])

    def test_infeasible_serial_and_empty_selection(self):
        from appliance_planner import plan_day
        with self.assertRaises(ValueError):plan_day(demo_forecast(),[],True)
        with self.assertRaises(ValueError):plan_day(demo_forecast(),[self.task('a',earliest=10,deadline=11),self.task('b',earliest=10,deadline=11)],False)

    def test_day_page_and_empty_selection(self):
        from app import app
        c=app.test_client()
        page=c.get('/day-planner').get_data(as_text=True)
        self.assertIn('live-solar-percent',page)
        self.assertIn('EV charging',page)
        self.assertIn('Sample forecast',page)
        page=c.get('/day-planner?submitted=1').get_data(as_text=True)
        self.assertIn('live-appliances',page)
        self.assertNotIn('type="checkbox" checked',page)
