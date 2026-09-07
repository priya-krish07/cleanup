# EcoPulse

EcoPulse is a Flask + SQLite community clean-up management platform. It includes event discovery, volunteer registration, organizer dashboards, waste tracking, impact scoring, a leaderboard, badges, and printable event reports.

## Run in VS Code

1. Install Python 3.11 or newer from https://www.python.org/downloads/ and enable **Add Python to PATH** during installation.
2. Open this folder in VS Code.
3. Create and activate a virtual environment in the VS Code terminal:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

5. Start the server:

   ```powershell
   py app.py
   ```

   Or double-click `run_ecopulse.bat` in the project folder. It creates the virtual environment, installs dependencies, starts Flask, and opens the browser automatically.

6. Open the local app at [http://127.0.0.1:5000](http://127.0.0.1:5000).

The SQLite database is created and seeded automatically on first start.

## Demo accounts

- Organizer: `admin@ecopulse.local` / `admin123`
- Volunteer: `nila@ecopulse.local` / `volunteer123`

## Main routes

- `/` public landing page
- `/events` event discovery and filters
- `/events/<id>` event details and volunteer registration
- `/events/<id>/manage` organizer tools for editing, deletion, tasks, and gallery images
- `/dashboard` organizer command center
- `/create-event` organizer event creation
- `/waste-tracker` organizer waste records
- `/impact` community impact score
- `/leaderboard` volunteer rankings
- `/profile` volunteer missions and badges
- `/report/<id>` printable event report
- `/notifications` signed-in volunteer notifications

## Notes

Images are loaded from Unsplash URLs so the demo has a polished visual presentation without bundling large binary assets. For production, configure a strong `SECRET_KEY`, serve uploaded media from a controlled storage location, and add CSRF protection before deploying.

## Deployment Procedures

### Local development

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

Open `http://127.0.0.1:5000`.

### Windows production-style run

Use Waitress instead of Flask's development server for a Windows deployment:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install waitress
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:FLASK_DEBUG = "false"
waitress-serve --listen=0.0.0.0:5000 app:app
```

Open `http://localhost:5000` on the server, or `http://SERVER-IP:5000` from another device on the same network. Add the port to Windows Firewall only when the app must be reachable from other devices.

### Render deployment

This repository includes `render.yaml` and `Procfile`.

1. Push the project to GitHub.
2. Sign in to Render and choose **New + → Blueprint**.
3. Select the GitHub repository and deploy the detected `render.yaml`.
4. Render runs `pip install -r requirements.txt`, then starts `gunicorn app:app`.
5. Open the generated Render URL.

The generated `SECRET_KEY` is configured automatically. Do not commit `database.db`, passwords, or API keys. SQLite is suitable for this demo, but production deployments should move to PostgreSQL because hosted disks may be ephemeral and multiple server instances cannot safely share a SQLite file.

### Frontend deployment note

There is no separate frontend build in this project. Flask serves the Jinja HTML templates and `static/` CSS/JavaScript from the same web service. Therefore deploy the backend service; the frontend is included automatically. External assets currently come from Google Fonts, Font Awesome, Chart.js CDN, and Unsplash.
