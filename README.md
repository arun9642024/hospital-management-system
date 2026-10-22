# Hospital Patient Data Analysis System

An educational Flask + MySQL application for operational analysis of **synthetic hospital visit data**. It summarizes visit volumes, department workload, monthly trends, and age-band distributions.

> **Important:** This project is for educational operational analytics only. It does not provide diagnoses or treatment advice. Use synthetic or properly de-identified data only. The UI displays record tables to authenticated users; reports exported from the app are aggregate-only.

## Features

- Login-protected dashboard
- MySQL tables for patients, departments, and visits
- Add synthetic patient and visit records
- Filter dashboard by date range
- Department workload, monthly trend, and age-band charts
- Daily visit summary statistics calculated with NumPy
- Aggregate department workload CSV export
- Basic form validation and parameterized SQL statements

## Technology stack

- Python 3.10+
- Flask
- MySQL 8+
- Pandas, NumPy, Matplotlib
- HTML, Bootstrap 5

## Folder structure

```text
hospital_patient_data_analysis_system/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── schema.sql
├── README.md
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── patients.html
│   ├── patient_form.html
│   ├── visits.html
│   ├── visit_form.html
│   └── error.html
└── static/
    └── css/
        └── style.css
```

## 1. Install prerequisites

Install:
1. Python 3.10 or newer
2. MySQL Server (and optionally MySQL Workbench)
3. Git

Check in PowerShell:

```powershell
python --version
git --version
```

## 2. Create and configure the database

Start MySQL Server. Open MySQL Workbench or a MySQL terminal, then run the full `schema.sql` file.

Alternatively, from the project folder, run:

```powershell
mysql -u root -p < schema.sql
```

Enter your MySQL password when prompted. The script creates the database, tables, departments, and synthetic demo records.

## 3. Configure environment variables

In PowerShell, from the project folder:

```powershell
Copy-Item .env.example .env
notepad .env
```

Set `DB_USER`, `DB_PASSWORD`, and `DB_NAME` to match your MySQL setup. Change `APP_PASSWORD` and `FLASK_SECRET_KEY` before using the app beyond local learning. Keep `.env` private; it is excluded from Git.

Generate a secret key with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the result into `FLASK_SECRET_KEY` in `.env`.

## 4. Create a virtual environment and install packages

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, for this terminal only you can run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 5. Run the application

```powershell
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

Sign in using the username and password you configured in `.env`:
- Username: value of `APP_USERNAME`
- Password: value of `APP_PASSWORD`

If you see a database connection error, confirm that MySQL is running, the database exists, and the `.env` connection values are correct.

## 6. Use the application

- **Dashboard:** use the date filters to review aggregate trends.
- **Patients:** view synthetic patient IDs and non-identifying age bands; add a synthetic patient.
- **Visits:** review recent visit records and add a visit.
- **Export report:** download an aggregate department workload CSV from the dashboard.

## 7. Push the project to GitHub

Create a new **empty** repository on GitHub (do not add a README or license there if you already have this local README). Then, in PowerShell from this project directory:

```powershell
git init
git add .
git status
git commit -m "Build hospital patient data analysis system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/hospital-patient-data-analysis-system.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. GitHub may ask you to authenticate through a browser or credential manager; use GitHub's supported sign-in flow, not your account password in the terminal.

Before committing, confirm `.env` is not listed by `git status`. If you accidentally staged it, run:

```powershell
git rm --cached .env
```

Then ensure `.env` is in `.gitignore`, and commit again. If `.env` was already pushed, treat its secrets as exposed and rotate them.

### If `origin` already exists

```powershell
git remote -v
git remote set-url origin https://github.com/YOUR-USERNAME/hospital-patient-data-analysis-system.git
git push -u origin main
```

## Troubleshooting

- `ModuleNotFoundError`: activate `.venv`, then run `pip install -r requirements.txt`.
- `Access denied for user`: correct `DB_USER` and `DB_PASSWORD` in `.env`.
- `Unknown database`: execute `schema.sql`.
- `Can't connect to MySQL server`: start the MySQL service and check `DB_HOST` / `DB_PORT`.
- PowerShell cannot activate venv: use the process-scoped execution policy command above.

## Security notes and limitations

This is a learning project, not a production healthcare system. Before any real deployment, use a production WSGI server, HTTPS, CSRF protection, proper role-based access, secure password storage and account management, rate limiting, audit logging, backups, and a formal privacy/security review. Never upload real patient data, credentials, or `.env` to GitHub.
