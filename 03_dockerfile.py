"""
LEKCE 03: Dockerfile — napises vlastni recept
===============================================
Zatim jsme pouzivali cizi image (nginx, ubuntu).
Ted si napises vlastni!

Dockerfile je soubor s instrukci jak postavit image.
Pises ho jednou, Docker ho pak vyroba kdykoli.

Naucis se:
  - psat Dockerfile od zacatku
  - pouzivat FROM, RUN, COPY, CMD, ENV, EXPOSE
  - postavit image: docker build
  - spustit vlastni image

Obtiznost: ⭐⭐
"""

import subprocess
import textwrap
from pathlib import Path


def docker_dostupny() -> bool:
    try:
        r = subprocess.run(["docker", "version"],
                          capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


DOCKER_OK = docker_dostupny()


# ══════════════════════════════════════════════════════════════
# CAST 1: Instrukce Dockerfile
# ══════════════════════════════════════════════════════════════

print("=== Instrukce Dockerfile ===\n")

instrukce = [
    ("FROM",       "Zakladni image ze ktereho stavime (vzdy prvni!)"),
    ("RUN",        "Spust prikaz behem buildu (nainstaluj balicky atd.)"),
    ("COPY",       "Zkopiruj soubory z pocitace do image"),
    ("ADD",        "Jako COPY, navic umí rozbaliovat archivy (pouzivej COPY)"),
    ("WORKDIR",    "Nastav pracovni adresar uvnitr image"),
    ("ENV",        "Nastav environment promennou"),
    ("EXPOSE",     "Dokumentuj ze kontejner posloucha na tomto portu"),
    ("CMD",        "Prikaz ktery se spusti kdyz startuje kontejner"),
    ("ENTRYPOINT", "Hlavni spustitelny program kontejneru"),
    ("ARG",        "Promenna dostupna behem buildu (ne za behu)"),
    ("USER",       "Spousted nasledujici prikazy jako tento uzivatel"),
    ("HEALTHCHECK","Jak overit ze kontejner opravdu funguje"),
    ("LABEL",      "Metadata image (verze, autor, popis)"),
]

for instrukce_name, popis in instrukce:
    print(f"  {instrukce_name:<14} — {popis}")


# ══════════════════════════════════════════════════════════════
# CAST 2: Prvni Dockerfile — jednoducha webova stranka
# ══════════════════════════════════════════════════════════════

print("\n=== Prvni Dockerfile — jednoducha stranka ===\n")

DOCKERFILE_JEDNODUCHY = """\
# Zakladni image: nginx s Alpine Linux (maly a rychly)
FROM nginx:alpine

# Zkopiruj nasi stranku dovnitr image
COPY index.html /usr/share/nginx/html/index.html

# nginx posloucha na portu 80
EXPOSE 80
"""

INDEX_HTML = """\
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <title>Moje stranka v Dockeru!</title>
  <style>
    body { font-family: sans-serif; text-align: center;
           background: #0d1117; color: #e6edf3; margin-top: 100px; }
    h1 { color: #58a6ff; font-size: 2.5rem; }
    p  { color: #8b949e; }
    .emoji { font-size: 4rem; }
  </style>
</head>
<body>
  <div class="emoji">🐳</div>
  <h1>Ahoj z Dockeru!</h1>
  <p>Tato stranka bezi uvnitr Docker kontejneru.</p>
  <p>Postavil jsem ji sam!</p>
</body>
</html>
"""

print("Soubor: Dockerfile")
print("-" * 50)
print(DOCKERFILE_JEDNODUCHY)
print("Soubor: index.html")
print("-" * 50)
print(INDEX_HTML[:300] + "...")


# ══════════════════════════════════════════════════════════════
# CAST 3: Python web aplikace
# ══════════════════════════════════════════════════════════════

print("\n=== Dockerfile pro Python aplikaci ===\n")

DOCKERFILE_PYTHON = """\
# Zakladni image: Python 3.12 slim (bez zbytecnych veci)
FROM python:3.12-slim

# Nastav pracovni adresar
WORKDIR /app

# Zkopiruj requirements a nainstaluj zavislosti
# (Delame to PRED kopirovani kodu — Docker cachuje vrstvy!)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Zkopiruj zdrojovy kod
COPY app.py .

# Port na kterem posloucha aplikace
EXPOSE 8000

# Spust aplikaci
CMD ["python", "app.py"]
"""

APP_PY = """\
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        odpoved = {
            "zprava": "Ahoj z Pythonu v Dockeru!",
            "cesta": self.path
        }
        self.wfile.write(json.dumps(odpoved).encode())
    def log_message(self, *args): pass  # ticho

print("Server bezi na http://localhost:8000")
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
"""

REQUIREMENTS = "# zatim prazdny — pouzivame jen stdlib\n"

print("Soubor: Dockerfile")
print("-" * 50)
print(DOCKERFILE_PYTHON)


# ══════════════════════════════════════════════════════════════
# CAST 4: Prikaz docker build
# ══════════════════════════════════════════════════════════════

print("=== Prikaz docker build ===\n")
print(textwrap.dedent("""\
  docker build -t moje-app:1.0 .
               │                │
               │                └─ build context (odkud brat soubory)
               └─ tag: jmeno:verze

  Dalsi moznosti:
    --no-cache          ← nepouzivej cache, vsechno znova
    --platform linux/amd64   ← pro krizove buildy (Apple Silicon)
    -f MujDockerfile    ← jiny nazev nez 'Dockerfile'
    --build-arg VAR=val ← predej hodnotu ARG instrukci
"""))


# ══════════════════════════════════════════════════════════════
# CAST 5: .dockerignore
# ══════════════════════════════════════════════════════════════

print("=== .dockerignore ===\n")

DOCKERIGNORE = """\
# Co NEchceme kopirovat do image:
__pycache__/
*.pyc
.venv/
venv/
.git/
.env
*.log
tests/
docs/
.pytest_cache/
node_modules/
"""

print(".dockerignore — soubory ktere se NEzkopirujou:")
print(DOCKERIGNORE)
print("Proc? Mensi image, zadna hesla v kodu, rychlejsi build.\n")


# ══════════════════════════════════════════════════════════════
# CAST 6: Stavba a spusteni
# ══════════════════════════════════════════════════════════════

if DOCKER_OK:
    print("=== Stavime image! ===\n")

    demo = Path("/tmp/docker_lekce03")
    demo.mkdir(exist_ok=True)

    # Zapis soubory
    (demo / "Dockerfile").write_text(DOCKERFILE_PYTHON)
    (demo / "app.py").write_text(APP_PY)
    (demo / "requirements.txt").write_text(REQUIREMENTS)

    # Build
    print("$ docker build -t moje-python-app:1.0 .")
    r = subprocess.run(
        ["docker", "build", "-t", "moje-python-app:1.0", "."],
        capture_output=True, text=True, cwd=str(demo)
    )
    if r.returncode == 0:
        print("  ✓ Image postavena!")

        # Zobraz velikost
        r2 = subprocess.run(
            ["docker", "images", "moje-python-app:1.0", "--format",
             "{{.Repository}}:{{.Tag}}  {{.Size}}"],
            capture_output=True, text=True
        )
        print(f"  Velikost: {r2.stdout.strip()}")

        # Spust
        print("\n$ docker run -d -p 8000:8000 --name lekce03 moje-python-app:1.0")
        r3 = subprocess.run(
            ["docker", "run", "-d", "-p", "8000:8000",
             "--name", "lekce03", "moje-python-app:1.0"],
            capture_output=True, text=True
        )
        if r3.returncode == 0:
            print("  ✓ Kontejner bezi!")
            print("  Otevri: http://localhost:8000")

        # Cleanup
        import time; time.sleep(1)
        subprocess.run(["docker", "stop", "lekce03"], capture_output=True)
        subprocess.run(["docker", "rm", "lekce03"], capture_output=True)
        subprocess.run(["docker", "rmi", "moje-python-app:1.0"], capture_output=True)
        print("\n  ✓ Cleanup dokoncen")
    else:
        print(f"  ✗ Build selhal: {r.stderr[:300]}")

    import shutil; shutil.rmtree(demo, ignore_errors=True)

else:
    print("=== Docker neni dostupny — ukazuji postup ===\n")
    print("  1. Vytvor slozku:  mkdir moje-app && cd moje-app")
    print("  2. Vytvor Dockerfile (viz vyse)")
    print("  3. Vytvor app.py (viz vyse)")
    print("  4. Sestaveni:  docker build -t moje-app:1.0 .")
    print("  5. Spusteni:   docker run -p 8000:8000 moje-app:1.0")
    print("  6. Otevri:     http://localhost:8000")


print("\n=== Hotovo! Dalsi lekce: Images a vrstvy ===")

# TVOJE ULOHA:
# 1. Vytvor slozku moje-web/ s Dockerfile (FROM nginx:alpine + COPY)
# 2. Sestav image prikazem docker build
# 3. Spust na portu 8080 a otevri v prohlizeci
# 4. Zmena: uprav index.html, sestav znova, reload prohlizece

# RESENI:
# 1. mkdir moje-web && echo '<h1>Ahoj!</h1>' > moje-web/index.html && echo -e 'FROM nginx:alpine\nCOPY index.html /usr/share/nginx/html/' > moje-web/Dockerfile
# 2. cd moje-web && docker build -t moje-web .
# 3. docker run -d -p 8080:80 moje-web  →  otevri http://localhost:8080
# 4. uprav index.html, pak: docker build -t moje-web . && docker rm -f $(docker ps -q --filter ancestor=moje-web) && docker run -d -p 8080:80 moje-web
