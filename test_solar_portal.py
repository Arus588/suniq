from contextlib import closing
import io
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app import create_app


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'accounts.sqlite3')
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret', 'DATABASE': self.path,
                               'GOOGLE_CLIENT_ID': None, 'GOOGLE_CLIENT_SECRET': None, 'PRESENTATION_LOGIN_ENABLED':True,
                               'ACCOUNT_EMAIL': '', 'ACCOUNT_PASSWORD_HASH': ''})
        with closing(sqlite3.connect(self.path)) as connection:
            connection.executemany('INSERT INTO users(id,google_sub,email,name) VALUES(?,?,?,?)',
                                  [(1,'one','one@example.com','One'),(2,'two','two@example.com','Two')])
            connection.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def login(self, user=1):
        with self.client.session_transaction() as state:
            state['user_id'] = user
            state['csrf'] = 'test-csrf'

    def post(self, url, **data):
        return self.client.post(url, data={'csrf_token':'test-csrf', **data}, follow_redirects=True)

    def setup_system(self, provider='enphase'):
        return self.post('/my-solar/setup', name='Home solar', provider=provider, site_id='home')

    def test_presentation_login_disabled(self):
        self.app.config['PRESENTATION_LOGIN_ENABLED']=False
        page=self.client.get('/signin').get_data(as_text=True)
        self.assertNotIn('arushbhingare2010@gmail.com',page)
        self.assertNotIn('gmail-accounts',page)
        self.assertEqual(self.client.post('/demo/signin',data={'csrf_token':'test-csrf'}).status_code,400)
        with self.client.session_transaction() as state:state['csrf']='test-csrf'
        self.assertEqual(self.client.post('/demo/signin',data={'csrf_token':'test-csrf','email':'arushbhingare2010@gmail.com'}).status_code,404)

    def test_password_account_with_presentation_disabled(self):
        from werkzeug.security import generate_password_hash
        self.app.config.update(PRESENTATION_LOGIN_ENABLED=False,
                               ACCOUNT_EMAIL='arushbhingare2010@gmail.com',
                               ACCOUNT_PASSWORD_HASH=generate_password_hash('test-password'))
        for email, password, mode in [('arushbhingare2010@gmail.com', 'wrong', 'login'),
                                      ('other@example.com', 'test-password', 'login'),
                                      ('arushbhingare2010@gmail.com', 'test-password', 'register')]:
            self.client.get('/signin')
            with self.client.session_transaction() as state:
                csrf = state['csrf']
            response = self.client.post('/access', data=dict(csrf_token=csrf, email=email,
                                        password=password, mode=mode, name='Arush'))
            self.assertEqual(response.location, '/signin')
            with self.client.session_transaction() as state:
                self.assertNotIn('password_authenticated', state)
        response = self.client.post('/access', data=dict(csrf_token=csrf,
                     email='ARUSHBHINGARE2010@gmail.com', password='test-password', mode='login'))
        self.assertEqual(response.location, '/demo/setup')
        self.assertEqual(self.client.get('/demo/setup').status_code, 200)
        self.assertEqual(self.client.get('/signin').location, '/demo/setup')
        with self.client.session_transaction() as state:
            self.assertTrue(state['password_authenticated'])
            self.assertNotIn('user_id', state)
            csrf = state['csrf']
        self.assertEqual(self.client.post('/demo/signin', data=dict(csrf_token=csrf,
                         email='arushbhingare2010@gmail.com')).status_code, 404)
        self.client.post('/demo/signout', data=dict(csrf_token=csrf))
        self.assertEqual(self.client.get('/demo/setup').location, '/signin')

    def test_default_page_and_logout(self):
        self.assertEqual(self.client.get('/').location, '/signin')
        self.assertIn('Sign in', self.client.get('/', follow_redirects=True).get_data(as_text=True))
        self.login()
        self.assertEqual(self.client.get('/').location, '/my-solar')
        self.assertEqual(self.client.get('/signin').location, '/my-solar')
        self.post('/logout')
        self.assertEqual(self.client.get('/').location, '/signin')

    def test_public_and_protected_routes(self):
        for path in ['/experiment', '/data', '/signin', '/privacy', '/my-solar/csv-template']:
            self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(self.client.get('/my-solar').location, '/signin')
        self.assertEqual(self.client.post('/my-solar/setup').status_code, 400)
        page = self.client.get('/signin').get_data(as_text=True)
        self.assertIn('Sign in', page)
        self.assertNotIn('awaiting administrator setup', page)

    def test_private_upload_and_account_isolation(self):
        self.login(); self.setup_system()
        timestamp = datetime.now(timezone.utc).isoformat()
        data=f'timestamp,generation_w,consumption_w\n{timestamp},2400,1100\n'
        response=self.post('/my-solar/import', readings=(io.BytesIO(data.encode()), 'readings.csv'))
        self.assertIn('Imported 1 readings',response.get_data(as_text=True))
        self.assertIn('+1.30 kW',response.get_data(as_text=True))
        self.login(2)
        page=self.client.get('/my-solar',follow_redirects=True).get_data(as_text=True)
        self.assertNotIn('+1.30 kW',page)
        self.setup_system()
        self.assertIn('No readings yet',self.client.get('/my-solar').get_data(as_text=True))

    def test_invalid_csv_is_atomic(self):
        self.login(); self.setup_system()
        data='timestamp,generation_w\n2026-10-01T12:00:00+00:00,1000\n2026-10-01T12:05:00+00:00,nan\n'
        result=self.post('/my-solar/import', readings=(io.BytesIO(data.encode()),'bad.csv'))
        self.assertIn('Import failed',result.get_data(as_text=True))
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM readings').fetchone()[0],0)
        for data in ['timestamp,generation_w\n2026-10-01T12:00:00,1000\n',
                     'timestamp,generation_w\n2026-10-01T12:00:00+00:00,100\n2026-10-01T12:00:00+00:00,200\n']:
            result=self.post('/my-solar/import', readings=(io.BytesIO(data.encode()),'bad.csv'))
            self.assertIn('Import failed',result.get_data(as_text=True))

    def test_provider_validation_and_deletion(self):
        self.login()
        self.assertEqual(self.post('/my-solar/setup', name='Home', provider='unknown').status_code,400)
        self.setup_system()
        self.assertEqual(self.post('/my-solar/delete').status_code,400)
        self.post('/my-solar/delete', confirm='delete')
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM users WHERE id=1').fetchone()[0],0)
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM systems').fetchone()[0],0)
        self.assertEqual(self.client.get('/my-solar').location,'/signin')

    def test_google_registration_and_returning_login(self):
        google=self.app.extensions['solar_google']
        identity={'sub':'new-google-user','email':'new@example.com','email_verified':True,'name':'New User'}
        with patch.object(google, 'authorize_access_token', return_value={'userinfo':identity}):
            result=self.client.get('/auth/google/callback')
            self.assertEqual(result.location,'/my-solar')
            self.client.get('/auth/google/callback')
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM users WHERE google_sub='new-google-user'").fetchone()[0],1)
        with self.client.session_transaction() as state:
            self.assertIsInstance(state['user_id'],int)
            self.assertNotIn('access_token',state)

    def test_unverified_identity_and_oauth_failure(self):
        google=self.app.extensions['solar_google']
        from authlib.integrations.base_client.errors import OAuthError
        with patch.object(google,'authorize_access_token',return_value={'userinfo':{'sub':'x','email':'x@x.com','email_verified':False}}):
            self.assertEqual(self.client.get('/auth/google/callback').location,'/signin')
        with patch.object(google,'authorize_access_token',side_effect=OAuthError()):
            self.assertEqual(self.client.get('/auth/google/callback').location,'/signin')
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM users').fetchone()[0],2)

    def test_provider_change_clears_previous_readings(self):
        self.login(); self.setup_system()
        self.post('/my-solar/import',readings=(io.BytesIO(b'timestamp,generation_w\n2026-10-01T12:00:00+00:00,100\n'),'good.csv'))
        self.setup_system('tesla')
        self.assertIn('No readings yet',self.client.get('/my-solar').get_data(as_text=True))

    def test_csrf_and_private_headers(self):
        self.login(); self.setup_system()
        self.assertEqual(self.client.post('/logout',data={'csrf_token':'wrong'}).status_code,400)
        response=self.client.get('/my-solar')
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual(response.headers['X-Frame-Options'],'DENY')
        self.assertNotIn('no-store',self.client.get('/').headers.get('Cache-Control',''))






    def test_demo_works_without_account_and_does_not_sign_in(self):
        for provider in ['enphase', 'tesla', 'invalid']:
            for scenario, expected in [('sunny', '+2.60 kW'), ('cloudy', '-0.70 kW'), ('evening', '-2.00 kW')]:
                page = self.client.get('/demo', query_string={'provider':provider,'scenario':scenario})
                self.assertEqual(page.status_code,200)
                self.assertIn(expected.split()[0],page.get_data(as_text=True))
                self.assertIn('Simulated data',page.get_data(as_text=True))
        with self.client.session_transaction() as state:
            self.assertNotIn('user_id',state)
        self.assertEqual(self.client.get('/my-solar').location,'/signin')

    def test_home_dashboard_has_no_scenario_buttons(self):
        page=self.client.get('/demo').get_data(as_text=True)
        self.assertNotIn('day-switcher',page)
        self.assertNotIn('Explore a scenario',page)
        self.assertNotIn('sensor-power-chart',page)

    def test_simulated_signin_and_inverter_registration(self):
        self.client.get('/signin')
        with self.client.session_transaction() as state:
            csrf=state['csrf']
        response=self.client.post('/demo/signin',data={'csrf_token':csrf,'email':'arushbhingare2010@gmail.com'})
        self.assertEqual(response.location,'/demo/setup')
        response=self.client.post('/demo/setup',data={'csrf_token':csrf,'name':'Garden home','provider':'solaredge','model':'SE7600H','serial':'DEMO-12345'},follow_redirects=True)
        page=response.get_data(as_text=True)
        self.assertIn('Garden home',page)
        self.assertIn('SE7600H',page)
        self.assertIn('SolarEdge',page)
        with self.client.session_transaction() as state:
            self.assertNotIn('user_id',state)
        self.assertEqual(self.client.get('/my-solar').location,'/signin')
        self.assertEqual(self.client.post('/demo/signout',data={'csrf_token':csrf}).location,'/signin')
        with self.client.session_transaction() as state:
            self.assertNotIn('demo_profile',state)
            self.assertNotIn('demo_system',state)

    def test_inverter_information_is_required(self):
        with self.client.session_transaction() as state:
            state['demo_profile']=True
            state['csrf']='test-csrf'
        for fields in [{}, {'model':'SE7600H'}, {'serial':'DEMO-12345'}, {'model':'  ','serial':'  '}]:
            response=self.client.post('/demo/setup',data={'csrf_token':'test-csrf','name':'Home','provider':'solaredge',**fields})
            self.assertEqual(response.status_code,400)
            with self.client.session_transaction() as state:
                self.assertNotIn('demo_system',state)


if __name__=='__main__': unittest.main()
