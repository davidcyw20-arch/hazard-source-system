param(
  [int]$Port = 5000,
  [string]$Host = "127.0.0.1",
  [string]$EnvFile = ".env",
  [switch]$SkipInstall,
  [switch]$SkipUpgrade,
  [switch]$SkipInitDb,
  [switch]$SeedDemo
)

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

function Import-DotEnv([string]$Path) {
  if (!(Test-Path $Path)) { return }
  Get-Content $Path | ForEach-Object {
    $line = $_.Trim()
    if ($line.Length -eq 0) { return }
    if ($line.StartsWith("#")) { return }
    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { return }
    $key = $line.Substring(0, $idx).Trim()
    $val = $line.Substring($idx + 1).Trim()
    if (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
      $val = $val.Substring(1, $val.Length - 2)
    }
    Set-Item -Path ("Env:{0}" -f $key) -Value $val
  }
}

Import-DotEnv -Path $EnvFile

function Assert-LastExit([string]$Step) {
  if ($LASTEXITCODE -ne 0) {
    throw "$Step failed (exit code=$LASTEXITCODE)."
  }
}

$venvPy = Join-Path $PSScriptRoot ".venv\\Scripts\\python.exe"
if (!(Test-Path $venvPy)) {
  $sysPy = (Get-Command python -ErrorAction SilentlyContinue)
  if (-not $sysPy) { throw "Python not found: install Python 3.11+ or add python to PATH." }
  Write-Host ">> Creating venv .venv ..."
  & $sysPy.Source -m venv .venv
  Assert-LastExit "Create venv"
}

if (-not $SkipInstall) {
  if (!(Test-Path (Join-Path $PSScriptRoot "requirements.txt"))) { throw "requirements.txt not found." }
  Write-Host ">> Installing requirements ..."
  & $venvPy -m pip install -r requirements.txt
  Assert-LastExit "Install requirements"
}

$env:FLASK_APP = "wsgi.py"
$env:FLASK_RUN_HOST = $Host
$env:FLASK_RUN_PORT = "$Port"

Write-Host ">> Checking MySQL connectivity / database / migrations ..."
$checkJson = @'
import json
import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

HEAD_REVISION = "20260105_01"

def _connect(url_str: str):
    engine = create_engine(url_str, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    engine.dispose()

def _try_create_db(url_str: str):
    url = make_url(url_str)
    dbname = url.database
    if not dbname:
        return False
    url_no_db = url.set(database=None)
    engine = create_engine(url_no_db, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{dbname}` DEFAULT CHARSET utf8mb4"))
            conn.execute(text("SELECT 1"))
        return True
    finally:
        engine.dispose()

def _alembic_status(url_str: str):
    engine = create_engine(url_str, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            schema = conn.execute(text("SELECT DATABASE()")).scalar_one()
            exists = conn.execute(text(
                "SELECT COUNT(1) FROM information_schema.tables "
                "WHERE table_schema=:s AND table_name='alembic_version'"
            ), {"s": schema}).scalar_one()
            if not exists:
                return {"exists": False, "revision": None, "at_head": False}
            rev = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one()
            return {"exists": True, "revision": rev, "at_head": (rev == HEAD_REVISION)}
    finally:
        engine.dispose()

def main():
    url = os.environ.get("DATABASE_URL") or ""
    if not url:
        url = "mysql+pymysql://root:root@127.0.0.1:3306/hazard_source_system?charset=utf8mb4"

    try:
        _connect(url)
        created = False
    except Exception as e:
        # Unknown database -> attempt create
        msg = str(e)
        if "Unknown database" in msg or "1049" in msg:
            created = _try_create_db(url)
            if created:
                _connect(url)
            else:
                raise
        else:
            raise

    st = _alembic_status(url)
    print(json.dumps({"ok": True, "db_created": created, "alembic": st}, ensure_ascii=False))

if __name__ == "__main__":
    main()
'@ | & $venvPy -
if ($LASTEXITCODE -ne 0) {
  Write-Host "!! MySQL check failed. Make sure MySQL is running and DATABASE_URL in .env is correct."
  Write-Host "   Example: DATABASE_URL=mysql+pymysql://root:root@127.0.0.1:3306/hazard_source_system?charset=utf8mb4"
  exit $LASTEXITCODE
}

$check = $checkJson | ConvertFrom-Json
if (-not $check.ok) { throw "Database check failed." }
if ($check.db_created) { Write-Host ">> Database created." }

if (-not $check.alembic.at_head) {
  if ($SkipUpgrade) {
    Write-Host "!! Migration is not at head (head=20260105_01), but upgrade is skipped."
  } else {
    Write-Host ">> Applying migrations (alembic upgrade head) ..."
    & $venvPy -m flask db-upgrade
    Assert-LastExit "DB upgrade"
  }
} else {
  Write-Host ">> Migrations OK (revision=$($check.alembic.revision))."
}

if (-not $SkipInitDb) {
  Write-Host ">> Running init-db (safe, no data deletion) ..."
  & $venvPy -m flask init-db
  Assert-LastExit "Init DB"
}

if ($SeedDemo) {
  Write-Host ">> Seeding demo data (no data deletion) ..."
  & $venvPy -m flask seed-demo
  Assert-LastExit "Seed demo"
}

Write-Host ">> Starting server: http://$Host`:$Port"
& $venvPy -m flask run --host $Host --port $Port
