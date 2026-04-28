"""
LEKCE 06: Docker Compose — orchestrace vice kontejneru
=======================================================
Realna aplikace neni jeden kontejner.
Ma web server, databazi, cache, worker...

Docker Compose ti umozni popsat vsechny sluzby
v jednom YAML souboru a spustit je jednim prikazem.

Naucis se:
  - psat docker-compose.yml
  - spoustet, zastavovat, logovat sluzby
  - sit mezi kontejnery
  - health checks a zavislosti

Obtiznost: ⭐⭐
"""

import subprocess
import textwrap
from pathlib import Path


def docker_dostupny() -> bool:
    try:
        r = subprocess.run(["docker", "compose", "version"],
                          capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


DOCKER_OK = docker_dostupny()


# ══════════════════════════════════════════════════════════════
# CAST 1: Proc Docker Compose?
# ══════════════════════════════════════════════════════════════

print("=== Proc Docker Compose? ===\n")

print(textwrap.dedent("""\
  Bez Compose — spustit web app s databazi:
    docker network create moje-sit
    docker volume create db-data
    docker run -d --name db --network moje-sit
               -v db-data:/var/lib/postgresql/data
               -e POSTGRES_PASSWORD=heslo postgres
    docker run -d --name web --network moje-sit
               -p 8000:8000
               -e DATABASE_URL=postgresql://postgres:heslo@db/app
               moje-web-app

  S Compose — totez jednim prikazem:
    docker compose up -d   ✅

  Navic:
    - vsechny sluzby v jednom souboru
    - automaticka sit mezi kontejnery
    - logy ze vsech najednou
    - jednoducha reprodukce prostredi
"""))


# ══════════════════════════════════════════════════════════════
# CAST 2: Anatomie docker-compose.yml
# ══════════════════════════════════════════════════════════════

print("=== Anatomie docker-compose.yml ===\n")

COMPOSE_ZAKLADNI = """\
services:          ← seznam vsech sluzeb (kontejneru)

  web:             ← jmeno sluzby
    build: .       ← sestav image z Dockerfile v aktualni slozce
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:heslo@db/app
    depends_on:
      db:
        condition: service_healthy   ← cekej az db bude zdravy

  db:              ← druha sluzba
    image: postgres:16-alpine        ← pouzij hotovou image
    environment:
      POSTGRES_PASSWORD: heslo
      POSTGRES_DB: app
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:           ← sdilene volumes
  db_data:
"""

print(COMPOSE_ZAKLADNI)


# ══════════════════════════════════════════════════════════════
# CAST 3: Sit mezi kontejnery
# ══════════════════════════════════════════════════════════════

print("=== Sit mezi kontejnery ===\n")

print(textwrap.dedent("""\
  Compose automaticky vytvorí sit pro vsechny sluzby.
  Kontejnery se navzajem vidí pod JMENEM SLUZBY.

  Priklad:
    web:  DATABASE_URL=postgresql://postgres:heslo@db/app
                                                    ^^
                                                    jmeno sluzby

  Nemusis resit IP adresy!
  db sluzi jako hostname — Docker resi DNS sam.

  Sit je izolována od ostatnich Compose projektu.
  Dve aplikace se navzajem nevidi (pokud neurcis jinak).
"""))


# ══════════════════════════════════════════════════════════════
# CAST 4: Plny priklad — web + db + redis + worker
# ══════════════════════════════════════════════════════════════

print("=== Plny priklad: web + db + redis + worker ===\n")

COMPOSE_PLNY = """\
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://admin:heslo@db/app
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=false
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: heslo
      POSTGRES_DB: app
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "admin"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  worker:
    build: .
    command: python worker.py
    environment:
      - DATABASE_URL=postgresql://admin:heslo@db/app
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

volumes:
  db_data:
  redis_data:
"""

print(COMPOSE_PLNY)


# ══════════════════════════════════════════════════════════════
# CAST 5: Prikazy Docker Compose
# ══════════════════════════════════════════════════════════════

print("=== Prikazy Docker Compose ===\n")

prikazy = [
    ("docker compose up",           "Spust vsechny sluzby (foreground)"),
    ("docker compose up -d",        "Spust vsechny sluzby (na pozadi)"),
    ("docker compose up web",       "Spust jen sluzbu 'web'"),
    ("docker compose down",         "Zastav a smaz kontejnery"),
    ("docker compose down -v",      "Zastav, smaz kontejnery I volumes"),
    ("docker compose ps",           "Stav vsech sluzeb"),
    ("docker compose logs",         "Logy vsech sluzeb"),
    ("docker compose logs -f web",  "Live logy sluzby 'web'"),
    ("docker compose restart web",  "Restartuj sluzbu 'web'"),
    ("docker compose exec web bash","Otevri terminal ve sluzbe 'web'"),
    ("docker compose build",        "Sestav vsechny images"),
    ("docker compose pull",         "Stahni nejnovejsi images"),
    ("docker compose config",       "Overuj konfiguraci (debug)"),
]

for cmd, popis in prikazy:
    print(f"  $ {cmd}")
    print(f"    → {popis}\n")


# ══════════════════════════════════════════════════════════════
# CAST 6: Demo
# ══════════════════════════════════════════════════════════════

if DOCKER_OK:
    print("=== Zkousime jednoduche Compose ===\n")

    demo = Path("/tmp/docker_compose_demo")
    demo.mkdir(exist_ok=True)

    APP_PY = """\
from http.server import HTTPServer, BaseHTTPRequestHandler
import os, json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        data = {
            "sluzba": os.getenv("SERVICE_NAME", "web"),
            "zprava": "Ahoj z Docker Compose!"
        }
        self.wfile.write(json.dumps(data).encode())
    def log_message(self, *args): pass

print("Server bezi na :8000")
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
"""

    DOCKERFILE = """\
FROM python:3.12-slim
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
"""

    COMPOSE = """\
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SERVICE_NAME=moje-web-app
"""

    (demo / "app.py").write_text(APP_PY)
    (demo / "Dockerfile").write_text(DOCKERFILE)
    (demo / "docker-compose.yml").write_text(COMPOSE)

    print("$ docker compose up -d")
    r = subprocess.run(["docker", "compose", "up", "-d", "--build"],
                      capture_output=True, text=True, cwd=str(demo))
    if r.returncode == 0:
        print("  ✓ Sluzby spusteny!")
        print("  Otevri http://localhost:8000")

        import time; time.sleep(2)
        print("\n$ docker compose ps")
        r2 = subprocess.run(["docker", "compose", "ps"],
                           capture_output=True, text=True, cwd=str(demo))
        print(r2.stdout.strip())
    else:
        print(f"  ✗ Chyba: {r.stderr[:200]}")

    print("\n$ docker compose down")
    subprocess.run(["docker", "compose", "down", "--rmi", "local"],
                   capture_output=True, cwd=str(demo))
    print("  ✓ Sluzby zastaveny")

    import shutil; shutil.rmtree(demo, ignore_errors=True)

else:
    print("=== Docker neni dostupny ===\n")
    print("  Nainstaluj Docker a vytvor docker-compose.yml dle prikladu vyse.")
    print("  Pak spust: docker compose up -d")


print("\n=== Hotovo! Dalsi lekce: Docker Hub a registry ===")

# TVOJE ULOHA:
# 1. Vytvor docker-compose.yml s nginx a postgres sluzba
# 2. Spust obe sluzby prikazem docker compose
# 3. Zobraz logy jen postgres sluzby
# 4. Zastav vsechno jednim prikazem

# RESENI:
# 1. viz priklad COMPOSE_ZAKLADNI vyse — uloz jako docker-compose.yml
# 2. docker compose up -d
# 3. docker compose logs -f db
# 4. docker compose down
