# SunIQ

SunIQ is a smart solar-energy system with a Flask web dashboard and Arduino firmware. It will use solar-panel measurements and simple predictions to help small off-grid systems decide when to run a load, conserve power, or charge a battery.

## Project goal

SunIQ helps small off-grid solar systems use energy wisely by extending useful battery operating time. It does this by measuring solar power, tracking historical readings, and recommending when to run or conserve energy-consuming loads.

## Project structure

```text
app.py                 Flask application
templates/             Dashboard HTML templates
static/                Dashboard styles and future JavaScript
firmware/              Arduino code (coming soon)
data/                  Recorded solar measurements (coming soon)
```

## Run locally

SunIQ requires Python 3.9 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in a browser.
