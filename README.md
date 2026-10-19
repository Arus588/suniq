# SunIQ

SunIQ is a smart solar-energy system with a Flask web dashboard and Arduino firmware. It will use solar-panel measurements and simple predictions to help small off-grid systems decide when to run a load, conserve power, or charge a battery.

## Project goal

SunIQ helps small off-grid solar systems use energy wisely by extending useful battery operating time. It does this by measuring solar power, tracking historical readings, and recommending when to run or conserve energy-consuming loads.

## Project structure

```text
app.py                 Flask application
prediction.py          Short-term power prediction and error calculation
capture_ina219.py       Save Arduino serial readings as new CSV sessions
templates/             Dashboard HTML templates
static/                Dashboard styles and future JavaScript
firmware/              Arduino sketch and wiring instructions
data/                  Recorded solar measurements
```

## Run locally

SunIQ requires Python 3.9 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in a browser. Signed-out visitors land on sign-in / registration; signed-in visitors go to their solar workspace. The public experiment is at `/experiment`.

## Capture new INA219 readings

After uploading the Arduino sketch, close Arduino IDE's Serial Monitor. In a separate terminal, find the Uno port with `python -m serial.tools.list_ports`, then run a capture (replace `COM3` with your port):

```powershell
python capture_ina219.py --port COM3 --scenario sun --orientation "fixed facing sun" --max-readings 20
```

The program saves each valid reading to a new CSV in `data/measurements/`. Use a different scenario such as `"hand shade"` for another condition. Omit `--max-readings` to keep recording until Ctrl+C. Open `http://127.0.0.1:5000/experiment?live=1` to refresh the dashboard every ten seconds. The next-reading prediction is calculated from each saved session after at least three readings. The capture program and Arduino Serial Monitor cannot use the same port at the same time.

The dashboard shows the last `captured_at` computer clock time. Its plot can show all readings, the last 5 or 15 minutes, the last hour, or a custom From/To time. Recent ranges are measured back from the latest saved reading. The older hand-pasted INA219 sessions have Arduino `timestamp_ms` values but no clock timestamps, so they appear only with All sessions.

## Google sign-in and personal solar accounts

SunIQ now includes:
- `/signin`: register or return using a Google account.
- `/my-solar/setup`: choose Enphase, SolarEdge, Tesla, Fronius, SMA, or Other and name a system.
- `/my-solar`: a private workspace with CSV import, generation/consumption comparison, and account deletion.
- `/privacy`: an explanation of stored account data.

Provider selection saves a preference, not a live API connection. This release imports provider exports after the user maps them to the SunIQ CSV format. It does not collect provider passwords or API keys, connect directly to rooftop wiring, or control equipment. The public Arduino experiment remains separate from account uploads.

### Enable Google sign-in locally

1. Install the updated dependencies in the project virtual environment:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env`. Generate a secret using:
   ```powershell
   .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
   ```
   Set `SUNIQ_SECRET_KEY` to that value. Do not share or commit it.
3. In Google Cloud Console, configure Google Auth Platform branding, audience, and a Web application OAuth client. During external testing, add the Google accounts that will test the app. Request only `openid email profile`.
4. Register this exact authorized redirect URI:
   `http://127.0.0.1:5000/auth/google/callback`
5. Put the client ID and secret in `.env` as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. Keep `GOOGLE_REDIRECT_URI` identical to the registered URI.
6. Run `.\.venv\Scripts\python.exe app.py`, then open `http://127.0.0.1:5000/signin`. First login creates the account; subsequent logins reuse it.

Without OAuth credentials, the app still runs and displays a setup-pending sign-in page. No fake login or authentication bypass is enabled. OAuth callback tests mock Google's verified identity response; a real Google authorization round-trip requires your configured OAuth client.

Google setup reference: https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid
Authlib integration reference: https://docs.authlib.org/en/latest/oauth2/client/web/flask.html

### Import readings

Download the example from the workspace. Supported columns:

```csv
timestamp,generation_w,consumption_w
2026-10-17T12:00:00+00:00,2400,1100
2026-10-17T12:05:00+00:00,2100,1300
```

These example values are illustrative, not measurements. Both power fields use watts; consumption is optional. Timestamps must include a timezone. Maximum upload: 2 MB and 10,000 rows. Invalid files are rejected before any readings are saved. Reimporting an existing timestamp updates it. Changing provider or site identifier clears the previous readings to avoid combining different systems. The dashboard shows the latest 100 records and explicitly labels old data; generation minus consumption does not establish grid export or battery flow.

### Hosting

Use HTTPS and set `SUNIQ_ENV=production`, a persistent `SUNIQ_SECRET_KEY` (at least 32 characters), and `GOOGLE_REDIRECT_URI=https://YOUR-DOMAIN/auth/google/callback`. Register that URI with Google too. Store OAuth secrets in the host's secret settings. Do not enable Flask debug mode on a public server. Use a production WSGI server; the included Gunicorn dependency is for Linux hosting.

SQLite account data is in ignored `instance/suniq.sqlite3`. Deploy on a single instance with a persistent disk for this prototype; ephemeral storage loses accounts and uploads. Do not publish the database. Google's app publishing/verification requirements depend on your configuration and audience. Live provider integration requires separate provider authorization, supported APIs, and securely managed tokens before it can be enabled.

### Verify

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

The tests cover existing experiments plus registration callbacks, rejection of unverified identity, per-user isolation, CSRF checks, provider validation, CSV validation, setup changes, and deletion. AI assistance used to build these features should be recorded in the competition disclosure; the student should understand and contribute to the implementation.

### No-login demonstration

Open `/demo` or choose **Try demo** on the sign-in page. Visitors can select a monitoring provider and sunny, cloudy, or evening scenarios using labeled sample readings. This creates no account, saves no readings, and grants no access to private workspaces. Google credentials are unnecessary for this demo.

### Presentation walkthrough

At `/signin`, **Continue** starts a separate demo session when Google is unconfigured. Register a system name, provider, and optional inverter model, then explore sunny/cloudy/evening energy scenarios. A small Demo badge identifies simulated data. No email, password, Google tokens, or real solar credentials are collected. Demo registration stays in the browser session and never authorizes access to private accounts. Sign out clears the demo setup.

## Appliance planner presentation build

Open `http://127.0.0.1:5000/planner` for the self-contained presentation. The sign-in and inverter walkthrough also leads to this page. This home app is independent of the Arduino experiment at `/experiment`.

Choose an appliance, earliest start, and finish-by time; optional settings customize average power and duration. The app checks all feasible half-hour starts, minimizes incremental appliance grid energy, and prefers the earliest start when estimates tie. It accounts for forecast household demand before assigning solar to the appliance. It displays task energy, solar/grid split, a surplus forecast chart, a comparison table, and session-local saved plans. Impossible deadlines produce an explanation instead of a fabricated result.

The forecast is an illustrative 48-slot day, not weather data, measured household data, or a live provider feed. Presets are adjustable average-power approximations, not appliance-specific cycle models. The model excludes batteries and prices, schedules one task at a time, and does not control appliances. Do not claim verified bill savings, live inverter connections, or achieved household outcomes. Saved plans persist only for the browser session.

Presentation sequence:
1. Explain the problem: solar readings alone do not answer when to run an appliance.
2. Choose dishwasher; earliest 8 AM, finish by 6 PM. Show the recommended start, solar coverage, and comparison against starting immediately.
3. Switch to EV charging to show how different power/duration changes the recommendation and remaining grid need.
4. Set an impossible window (three-hour task, 5 PM to 6 PM) to show deadline validation.
5. Expand Why this time to explain the half-hour search and household-load reservation, then save a plan.
6. Explain your coding contributions, testing, AI assistance, limitations, and next step: one real provider/forecast integration and measured evaluation.

Run `python -m unittest discover -v` in the configured virtual environment for planner calculations, account isolation, validation, and original experiment tests.

## Shared daily appliance schedule

Open `/day-planner` to select up to four appliances, set each earliest start/deadline, adjust average power/duration, and choose parallel or sequential runs. The schedule shows overlaps and combined solar/grid energy. Solar remaining after household demand is shared once per half-hour across all tasks. The bounded search considers task-order permutations and improves starts; it is a heuristic, not a guaranteed global optimum. All tasks are uninterrupted, scheduled once, and constrained to the same illustrative day. Home circuit limits, battery behavior, appliance-cycle variation and tariffs are not modeled. The parallel option grants scheduling flexibility, not a guarantee that appliances should overlap. The single-task planner remains at `/planner`.

### Presentation login and deployment

The presentation account chooser is disabled by default. Set `SUNIQ_PRESENTATION_LOGIN=true` only for local presentations. Deploy with `SUNIQ_ENV=production`, a persistent secret, and Google OAuth credentials. Production forcibly disables the presentation chooser and rejects its sign-in endpoint, even if the presentation flag is true. Real sign-in remains Google-verified.

## Current registration presentation flow

The entry page now offers Login (email/password) and Register (name/email/password). When explicitly enabled with `SUNIQ_PRESENTATION_LOGIN=true` in a nonproduction environment, the configured Arush account opens the presentation workspace without password verification. Other submissions show a registration-pending screen; passwords and pending requests are not saved and no outreach email is sent. This is not a completed password-authentication system. Production forcibly disables presentation access. Real public registration requires password hashing, persistent account/request storage, approval handling, and authentication before deployment. The existing Google OAuth backend remains available for later integration, but Google buttons are not part of the current entry screen.
