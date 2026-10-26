"""Google identity and private solar workspaces; no provider passwords collected."""
import csv
import io
import math
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from werkzeug.security import check_password_hash

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, session, url_for

PROVIDERS = {
    'enphase': ('Enphase', 'Enlighten monitoring'),
    'solaredge': ('SolarEdge', 'SolarEdge monitoring'),
    'tesla': ('Tesla', 'Solar and Powerwall'),
    'fronius': ('Fronius', 'Solar.web monitoring'),
    'sma': ('SMA', 'Sunny Portal monitoring'),
    'other': ('Other / not sure', 'Start with a CSV export'),
}
portal = Blueprint('portal', __name__)


def db():
    if 'solar_db' not in g:
        g.solar_db = sqlite3.connect(current_app.config['DATABASE'])
        g.solar_db.row_factory = sqlite3.Row
        g.solar_db.execute('PRAGMA foreign_keys=ON')
    return g.solar_db


def csrf_token():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    return session['csrf']


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user:
            return redirect(url_for('portal.signin'))
        return view(*args, **kwargs)
    return wrapped


def init_portal(app, test_config=None):
    from dotenv import load_dotenv
    load_dotenv(Path(app.root_path) / '.env')
    configured_secret = os.getenv('SUNIQ_SECRET_KEY')
    production = os.getenv('SUNIQ_ENV') == 'production'
    if production and (not configured_secret or len(configured_secret) < 32):
        raise RuntimeError('Set a SUNIQ_SECRET_KEY of at least 32 characters for production')
    app.config.update(
        SECRET_KEY=configured_secret or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=production,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
        DATABASE=str(Path(app.instance_path) / 'suniq.sqlite3'),
        PRESENTATION_LOGIN_ENABLED=(not production and os.getenv('SUNIQ_PRESENTATION_LOGIN','').lower()=='true'),
        ACCOUNT_EMAIL=os.getenv('SUNIQ_ACCOUNT_EMAIL', '').strip().casefold(),
        ACCOUNT_PASSWORD_HASH=os.getenv('SUNIQ_ACCOUNT_PASSWORD_HASH', ''),
        GOOGLE_CLIENT_ID=os.getenv('GOOGLE_CLIENT_ID'),
        GOOGLE_CLIENT_SECRET=os.getenv('GOOGLE_CLIENT_SECRET'),
        GOOGLE_REDIRECT_URI=os.getenv('GOOGLE_REDIRECT_URI', 'http://127.0.0.1:5000/auth/google/callback'),
    )
    if test_config:
        app.config.update(test_config)
    if production:
        app.config['PRESENTATION_LOGIN_ENABLED']=False
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    with app.app_context():
        db().executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, google_sub TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL, name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS systems (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL, provider TEXT NOT NULL, site_id TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS readings (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            timestamp TEXT NOT NULL, generation_w REAL NOT NULL, consumption_w REAL,
            PRIMARY KEY(user_id,timestamp));
        ''')
    @app.teardown_appcontext
    def close_db(error=None):
        connection = g.pop('solar_db', None)
        if connection is not None:
            connection.close()
    @app.before_request
    def account_context():
        g.user = None
        if session.get('user_id'):
            g.user = db().execute('SELECT id,email,name FROM users WHERE id=?', (session['user_id'],)).fetchone()
        if request.method == 'POST':
            supplied = request.form.get('csrf_token', '')
            if not supplied or not secrets.compare_digest(supplied, session.get('csrf', '')):
                abort(400, 'Your form expired. Refresh the page and try again.')
    @app.context_processor
    def account_template_context():
        return dict(current_user=g.user, csrf_token=csrf_token)
    @app.after_request
    def protect_account_pages(response):
        if request.blueprint == 'portal':
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Referrer-Policy'] = 'same-origin'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
        return response
    from authlib.integrations.flask_client import OAuth
    oauth = OAuth(app)
    oauth.register('google', client_id=app.config['GOOGLE_CLIENT_ID'],
                   client_secret=app.config['GOOGLE_CLIENT_SECRET'],
                   server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                   client_kwargs={'scope': 'openid email profile'})
    app.extensions['solar_google'] = oauth.google
    app.register_blueprint(portal)


@portal.get('/privacy')
def privacy():
    return render_template('privacy.html')


@portal.get('/about')
def about():
    return render_template('about.html')


@portal.get('/signin')
def signin():
    if g.user:
        return redirect(url_for('portal.workspace'))
    if session.get('demo_profile') and (session.get('password_authenticated') or current_app.config['PRESENTATION_LOGIN_ENABLED']):
        return redirect(url_for('portal.demo') if session.get('demo_system') else url_for('portal.demo_setup'))
    ready = bool(current_app.config['GOOGLE_CLIENT_ID'] and current_app.config['GOOGLE_CLIENT_SECRET'])
    return render_template('signin.html', mode='register' if request.args.get('mode')=='register' else 'login')


@portal.post('/auth/google')
def google_login():
    if not current_app.config['GOOGLE_CLIENT_ID'] or not current_app.config['GOOGLE_CLIENT_SECRET']:
        flash('Google sign-in is awaiting setup by the SunIQ administrator.', 'error')
        return redirect(url_for('portal.signin'))
    session.clear()
    return current_app.extensions['solar_google'].authorize_redirect(current_app.config['GOOGLE_REDIRECT_URI'], prompt='select_account')


@portal.get('/auth/google/callback')
def google_callback():
    from authlib.integrations.base_client.errors import OAuthError
    from authlib.jose.errors import JoseError
    from requests.exceptions import RequestException
    try:
        token = current_app.extensions['solar_google'].authorize_access_token()
        identity = token.get('userinfo')
        if not identity or not identity.get('sub') or not identity.get('email') or identity.get('email_verified') is not True:
            raise ValueError('Verified identity required')
    except (OAuthError, JoseError, RequestException, ValueError):
        session.clear()
        flash('Google sign-in could not be completed. Please try again.', 'error')
        return redirect(url_for('portal.signin'))
    connection = db()
    with connection:
        connection.execute('''INSERT INTO users(google_sub,email,name) VALUES(?,?,?)
            ON CONFLICT(google_sub) DO UPDATE SET email=excluded.email,name=excluded.name''',
            (identity['sub'], identity['email'], identity.get('name') or identity['email']))
    user = connection.execute('SELECT id FROM users WHERE google_sub=?', (identity['sub'],)).fetchone()
    session.clear()
    session['user_id'] = user['id']
    session.permanent = True
    return redirect(url_for('portal.workspace'))


@portal.post('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard'))


@portal.route('/my-solar/setup', methods=['GET', 'POST'])
@login_required
def setup():
    system = db().execute('SELECT * FROM systems WHERE user_id=?', (g.user['id'],)).fetchone()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        provider = request.form.get('provider', '')
        site_id = request.form.get('site_id', '').strip()
        if not name or len(name) > 80 or provider not in PROVIDERS or len(site_id) > 120:
            flash('Enter a system name (up to 80 characters) and choose a provider.', 'error')
            return render_template('solar_setup.html', providers=PROVIDERS, system=request.form), 400
        connection = db()
        with connection:
            if system and (system['provider'] != provider or system['site_id'] != site_id):
                connection.execute('DELETE FROM readings WHERE user_id=?', (g.user['id'],))
            connection.execute('''INSERT INTO systems(user_id,name,provider,site_id) VALUES(?,?,?,?)
                ON CONFLICT(user_id) DO UPDATE SET name=excluded.name,provider=excluded.provider,site_id=excluded.site_id''',
                (g.user['id'], name, provider, site_id))
        flash('Your solar setup is saved. Import readings to see your energy data.', 'success')
        return redirect(url_for('portal.workspace'))
    return render_template('solar_setup.html', providers=PROVIDERS, system=system)


@portal.get('/my-solar')
@login_required
def workspace():
    system = db().execute('SELECT * FROM systems WHERE user_id=?', (g.user['id'],)).fetchone()
    if not system:
        return redirect(url_for('portal.setup'))
    readings = db().execute('SELECT * FROM readings WHERE user_id=? ORDER BY timestamp DESC LIMIT 100', (g.user['id'],)).fetchall()
    latest = readings[0] if readings else None
    surplus = latest['generation_w'] - latest['consumption_w'] if latest and latest['consumption_w'] is not None else None
    stale = bool(latest and (datetime.now(timezone.utc) - datetime.fromisoformat(latest['timestamp'])).total_seconds() > 900)
    return render_template('solar_workspace.html', system=system, provider_name=PROVIDERS[system['provider']][0],
                           readings=readings, latest=latest, surplus=surplus, stale=stale)


@portal.post('/my-solar/import')
@login_required
def import_readings():
    if not db().execute('SELECT 1 FROM systems WHERE user_id=?', (g.user['id'],)).fetchone():
        return redirect(url_for('portal.setup'))
    uploaded = request.files.get('readings')
    try:
        if not uploaded or not uploaded.filename.lower().endswith('.csv'):
            raise ValueError('Choose a CSV file.')
        reader = csv.DictReader(io.StringIO(uploaded.read().decode('utf-8-sig')))
        if not {'timestamp', 'generation_w'}.issubset(reader.fieldnames or []):
            raise ValueError('Required CSV columns: timestamp, generation_w. Optional: consumption_w.')
        parsed = []; seen = set()
        for index, row in enumerate(reader, start=2):
            if index > 10001:
                raise ValueError('Upload at most 10,000 readings at a time.')
            timestamp = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            if timestamp.utcoffset() is None:
                raise ValueError('Each timestamp must include a timezone, such as +00:00.')
            timestamp = timestamp.astimezone(timezone.utc)
            if timestamp > datetime.now(timezone.utc) + timedelta(minutes=5):
                raise ValueError('Readings cannot be in the future.')
            timestamp = timestamp.isoformat()
            if timestamp in seen:
                raise ValueError('Duplicate timestamps found in this file.')
            seen.add(timestamp)
            generation = float(row['generation_w'])
            consumption = float(row['consumption_w']) if row.get('consumption_w', '').strip() else None
            if any(not math.isfinite(v) or v < 0 or v > 1000000 for v in (generation, consumption) if v is not None):
                raise ValueError('Power must be a finite, nonnegative number in watts, up to 1,000,000.')
            parsed.append((g.user['id'], timestamp, generation, consumption))
        if not parsed:
            raise ValueError('The file contains no readings.')
    except (ValueError, UnicodeError, KeyError, TypeError, AttributeError, csv.Error) as error:
        flash('Import failed. ' + (str(error) if isinstance(error, ValueError) else 'Check your CSV format.'), 'error')
        return redirect(url_for('portal.workspace'))
    connection = db()
    with connection:
        connection.executemany('''INSERT INTO readings VALUES(?,?,?,?) ON CONFLICT(user_id,timestamp)
            DO UPDATE SET generation_w=excluded.generation_w,consumption_w=excluded.consumption_w''', parsed)
    flash(f'Imported {len(parsed)} readings. These are uploaded records, not a live connection.', 'success')
    return redirect(url_for('portal.workspace'))


@portal.get('/my-solar/csv-template')
def csv_template():
    from flask import Response
    return Response('timestamp,generation_w,consumption_w\n2026-10-17T12:00:00+00:00,2400,1100\n2026-10-17T12:05:00+00:00,2100,1300\n',
                    mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=suniq-example.csv'})


@portal.post('/my-solar/delete')
@login_required
def delete_account():
    if request.form.get('confirm') != 'delete':
        abort(400, 'Confirm account deletion first.')
    connection = db()
    with connection:
        connection.execute('DELETE FROM users WHERE id=?', (g.user['id'],))
    session.clear()
    flash('Your SunIQ account and uploaded readings have been deleted.', 'success')
    return redirect(url_for('portal.signin'))


@portal.get('/demo')
@portal.get('/energy')
def demo():
    system = session.get('demo_system', {})
    provider = request.args.get('provider', system.get('provider', 'enphase'))
    if provider not in PROVIDERS:
        provider = 'other'
    scenario = request.args.get('scenario', 'sunny')
    samples = {'sunny': 4200, 'cloudy': 900, 'evening': 100}
    if scenario not in samples:
        scenario = 'sunny'
    generation = samples[scenario]
    running_appliances = [
        dict(name='Air conditioning', watts=1200),
        dict(name='Refrigerator', watts=150),
        dict(name='TV', watts=100),
        dict(name='Lights', watts=100),
        dict(name='Router and standby devices', watts=50),
    ]
    if scenario == 'evening':
        running_appliances.append(dict(name='Cooking appliances (average)', watts=500))
    consumption = sum(item['watts'] for item in running_appliances)
    from appliance_planner import demo_forecast, STEP, clock
    forecast = demo_forecast()
    best_start = max(range(45), key=lambda i: sum(max(0, r['solar_kw']-r['home_kw']) for r in forecast[i:i+4]))
    best_window = f"{clock(best_start*STEP)} - {clock((best_start+4)*STEP)}"
    solar_kwh = sum(r['solar_kw'] * STEP for r in forecast)
    home_kwh = sum(r['home_kw'] * STEP for r in forecast)
    grid_kwh = sum(max(0, r['home_kw'] - r['solar_kw']) * STEP for r in forecast)
    week = [dict(day=day, solar=round(solar_kwh*s, 1), usage=round(home_kwh*u, 1))
            for day, s, u in [('Mon', .85, .95), ('Tue', .65, 1.1), ('Wed', 1, 1),
                              ('Thu', .7, .9), ('Fri', .95, 1.05), ('Sat', .8, 1.2), ('Sun', 1, 1)]]
    return render_template('solar_demo.html', system=system, providers=PROVIDERS, provider=provider,
                           scenario=scenario, generation=generation, consumption=consumption,
                           running_appliances=running_appliances,
                           surplus=generation-consumption, solar_kwh=solar_kwh, home_kwh=home_kwh,
                           grid_kwh=grid_kwh, cost=grid_kwh*.30, week=week,
                           chart_max=max(max(d['solar'], d['usage']) for d in week),
                           forecast=forecast, best_start=best_start, best_window=best_window, clock=clock)


@portal.post('/demo/signin')
def demo_signin():
    if not current_app.config['PRESENTATION_LOGIN_ENABLED'] or current_app.config['ACCOUNT_PASSWORD_HASH']:
        abort(404)
    email=request.form.get('email','').strip().casefold()
    if email!='arushbhingare2010@gmail.com':
        flash('Please sign in with your Gmail account.','error')
        return redirect(url_for('portal.signin'))
    session['display_name']='Arush B'
    session['presentation_email']=email
    session['demo_profile'] = True
    return redirect(url_for('portal.demo') if session.get('demo_system') else url_for('portal.demo_setup'))


@portal.route('/demo/setup', methods=['GET', 'POST'])
def demo_setup():
    if not session.get('demo_profile') or not (session.get('password_authenticated') or current_app.config['PRESENTATION_LOGIN_ENABLED']):
        return redirect(url_for('portal.signin'))
    system = session.get('demo_system', {})
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        provider = request.form.get('provider', '')
        model = request.form.get('model', '').strip()
        serial = request.form.get('serial', '').strip()
        if not name or len(name)>80 or provider not in PROVIDERS or not model or len(model)>80 or not serial or len(serial)>120:
            flash('Select a provider and enter your inverter model and serial number.', 'error')
            return render_template('demo_setup.html', providers=PROVIDERS, system=request.form), 400
        session['demo_system'] = dict(name=name, provider=provider, model=model, serial=serial)
        return redirect(url_for('portal.demo'))
    return render_template('demo_setup.html', providers=PROVIDERS, system=system)


@portal.post('/demo/signout')
def demo_signout():
    session.pop('password_authenticated', None)
    session.pop('demo_profile', None)
    session.pop('display_name',None)
    session.pop('presentation_email',None)
    session.pop('demo_system', None)
    session.pop('latest_appliance_plan',None)
    session.pop('saved_appliance_plan',None)
    session.pop('run_history',None)
    return redirect(url_for('portal.signin'))


@portal.route('/planner', methods=['GET', 'POST'])
def planner():
    from appliance_planner import APPLIANCES, demo_forecast, plan_appliance, clock
    if request.method == 'POST':
        plan=session.get('latest_appliance_plan')
        if not plan:
            flash('Create a plan before saving.', 'error')
        else:
            session['saved_appliance_plan']=plan
            flash('Plan saved for this browser session.', 'success')
        return redirect(url_for('portal.planner',**session.get('latest_appliance_inputs',{})))
    appliance=request.args.get('appliance','dishwasher')
    if appliance not in APPLIANCES: appliance='dishwasher'
    preset=APPLIANCES[appliance]
    defaults=dict(power=preset['power_kw'],duration=preset['duration_hours'],earliest=8.0,deadline=18.0)
    settings={key:request.args.get(key,str(value)) for key,value in defaults.items()}
    error=None; result=None
    forecast=demo_forecast()
    try:
        numbers={key:float(value) for key,value in settings.items()}
        result=plan_appliance(forecast,numbers['power'],numbers['duration'],numbers['earliest'],numbers['deadline'])
        session['latest_appliance_inputs']=dict(appliance=appliance,**settings)
        session['latest_appliance_plan']=dict(appliance=preset['name'],start=result['start_label'],end=result['end_label'],grid_kwh=round(result['grid_kwh'],2))
    except (ValueError,TypeError) as exc:
        error=str(exc)
        session.pop('latest_appliance_plan',None)
    chart=[]
    for row in forecast[12:44]:
        hour=row['hour']
        chart.append(dict(label=clock(hour),height=round(100*max(0,row['solar_kw']-row['home_kw'])/4.5,2),
                          selected=bool(result and result['start']<=hour<result['end'])))
    return render_template('planner.html',appliances=APPLIANCES,appliance=appliance,settings=settings,
                           result=result,error=error,chart=chart,clock=clock,
                           saved=session.get('saved_appliance_plan'),
                           system=session.get('demo_system',{}),providers=PROVIDERS)

@portal.get('/day-planner')
def day_planner():
    from appliance_planner import APPLIANCES, demo_forecast, plan_day, clock
    selected=request.args.getlist('task') if 'submitted' in request.args else ['dishwasher','washer','ev']
    selected=list(dict.fromkeys(selected))
    parallel=request.args.get('parallel','yes')=='yes'
    settings={};tasks=[];error=None;result=None
    try:
        if any(key not in APPLIANCES for key in selected):raise ValueError('Choose a supported appliance.')
        for key,preset in APPLIANCES.items():
            settings[key]=dict(earliest=request.args.get(key+'_earliest','8'),deadline=request.args.get(key+'_deadline','18'),
                               power=request.args.get(key+'_power',str(preset['power_kw'])),duration=request.args.get(key+'_duration',str(preset['duration_hours'])))
            if key in selected:
                fields=settings[key]
                tasks.append(dict(id=key,name=preset['name'],power_kw=float(fields['power']),duration_hours=float(fields['duration']),
                                  earliest=float(fields['earliest']),deadline=float(fields['deadline'])))
        result=plan_day(demo_forecast(),tasks,parallel)
    except (ValueError,TypeError) as exc:error=str(exc)
    return render_template('day_planner.html',appliances=APPLIANCES,selected=selected,settings=settings,parallel=parallel,
                           result=result,error=error,clock=clock,forecast=demo_forecast())

@portal.post('/activity/complete')
def complete_activity():
    from appliance_planner import APPLIANCES, demo_forecast, plan_appliance, clock
    key=request.form.get('appliance','')
    try:
        if key not in APPLIANCES: raise ValueError('Choose a supported appliance.')
        power=float(request.form.get('power',''))
        duration=float(request.form.get('duration',''))
        earliest=float(request.form.get('earliest',''))
        actual=float(request.form.get('actual',''))
        rate=float(request.form.get('import_rate','0.30'))
        export=float(request.form.get('export_rate','0.08'))
        if not all(math.isfinite(v) and 0<=v<=5 for v in (rate,export)):
            raise ValueError('Enter electricity rates between $0 and $5 per kWh.')
        baseline=plan_appliance(demo_forecast(),power,duration,earliest,earliest+duration)
        run=plan_appliance(demo_forecast(),power,duration,actual,actual+duration)
        cost=run['grid_kwh']*rate+run['solar_kwh']*export
        baseline_cost=baseline['grid_kwh']*rate+baseline['solar_kwh']*export
    except (ValueError,TypeError) as exc:
        flash(str(exc),'error')
        return redirect(url_for('portal.day_planner'))
    # User-confirmed runs with modeled energy, never presented as meter readings.
    record=dict(name=APPLIANCES[key]['name'],start=clock(actual),end=clock(actual+duration),
                energy=round(run['energy_kwh'],2),solar_percent=round(run['solar_percent'],1),
                cost=round(cost,2),difference=round(baseline_cost-cost,2),baseline=clock(earliest),
                recorded=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
                import_rate=rate,export_rate=export)
    history=session.get('run_history',[])
    session['run_history']=[record]+history[:7]
    flash('Run recorded. Energy and cost are estimates, not measured results.','success')
    return redirect(url_for('portal.day_planner')+'#recent-runs')


@portal.post('/access')
def access_request():
    mode=request.form.get('mode','login')
    email=request.form.get('email','').strip().casefold()
    password=request.form.get('password','')
    name=request.form.get('name','').strip()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(email)>254 or not password or len(password)>256 or (mode=='register' and (not name or len(name)>80)):
        flash('Enter a valid email, password, and your name when registering.','error')
        return redirect(url_for('portal.signin',mode=mode))
    password_hash = current_app.config['ACCOUNT_PASSWORD_HASH']
    if password_hash and email == current_app.config['ACCOUNT_EMAIL']:
        if mode != 'login' or not check_password_hash(password_hash, password):
            flash('Email or password is incorrect.', 'error')
            return redirect(url_for('portal.signin'))
        session.clear()
        session.permanent = True
        session['password_authenticated'] = True
        session['display_name'] = 'Arush B'
        session['presentation_email'] = email
        session['demo_profile'] = True
        return redirect(url_for('portal.demo_setup'))
    if password_hash and mode == 'login':
        flash('Email or password is incorrect.', 'error')
        return redirect(url_for('portal.signin'))
    if email=='arushbhingare2010@gmail.com' and current_app.config['PRESENTATION_LOGIN_ENABLED']:
        session.clear()
        session['display_name']='Arush B'
        session['presentation_email']=email
        session['demo_profile']=True
        return redirect(url_for('portal.demo_setup'))
    # No authenticated account is created; do not retain the submitted password.
    return render_template('registration_pending.html',name=name,email=email)
