"""
Generátor webu pro Docker & Kubernetes kurz
=============================================
Precte vsechny lekce (01_*.py ... 15_*.py),
vygeneruje HTML stranky do slozky web/.

Spusteni:
    python3 generator_webu.py

Pak otevri:
    web/index.html
nebo spust server:
    cd web && python3 -m http.server 8080
    → http://localhost:8080
"""

import ast
import html
import json
import re
import textwrap
import unicodedata
from pathlib import Path

zde = Path(__file__).parent

# ══════════════════════════════════════════════════════════════
# Pomocne funkce
# ══════════════════════════════════════════════════════════════

def ascii_stem(stem: str) -> str:
    norm = unicodedata.normalize("NFD", stem)
    return "".join(c for c in norm if unicodedata.category(c) != "Mn")


def nacti_lekci(cesta: Path) -> dict:
    kod = cesta.read_text(encoding="utf-8")
    try:
        strom = ast.parse(kod)
        docstring = ast.get_docstring(strom) or ""
    except SyntaxError:
        docstring = ""

    radky = docstring.splitlines()
    titul = radky[0].strip() if radky else cesta.stem

    obtiznost = ""
    for r in radky:
        hvezdy = r.count("⭐")
        if hvezdy:
            obtiznost = "⭐" * hvezdy
            break

    m = re.match(r"(\d+)_", cesta.stem)
    cislo = int(m.group(1)) if m else 0

    ulohy = []
    reseni = []
    sekce = None
    for radek in kod.splitlines():
        stripped = radek.strip()
        if stripped.startswith("# TVOJE ULOHA") or stripped.startswith("# TVOJE ULOA"):
            sekce = "ulohy"
        elif stripped.startswith("# RESENI"):
            sekce = "reseni"
        elif sekce == "ulohy" and stripped.startswith("# ") and stripped[2:3].isdigit() and ". " in stripped:
            ulohy.append(stripped[2:])
        elif sekce == "reseni" and stripped.startswith("# "):
            text = stripped[2:].strip()
            if text:
                reseni.append(text)

    return {
        "cislo":     cislo,
        "soubor":    cesta.name,
        "stem":      cesta.stem,
        "slug":      ascii_stem(cesta.stem),
        "titul":     titul,
        "docstring": docstring,
        "obtiznost": obtiznost or "⭐",
        "ulohy":     ulohy,
        "reseni":    reseni,
        "kod":       kod,
    }


# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════

CSS = """
:root {
  --bg: #0d1117; --surface: #161b22; --border: #30363d;
  --text: #e6edf3; --muted: #8b949e; --accent: #58a6ff;
  --green: #3fb950; --yellow: #d29922; --red: #f85149;
  --code-bg: #1c2128;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text);
       font-family: 'Segoe UI', system-ui, sans-serif;
       line-height: 1.6; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

header { background: var(--surface); border-bottom: 1px solid var(--border);
         padding: 1rem 2rem; display: flex; align-items: center; gap: 1rem; }
header h1 { font-size: 1.4rem; }
header .badge { background: var(--accent); color: #000;
                padding: .2rem .6rem; border-radius: 999px;
                font-size: .75rem; font-weight: 700; }

main { max-width: 960px; margin: 2rem auto; padding: 0 1.5rem; }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr));
        gap: 1rem; margin-top: 1.5rem; }
.card { background: var(--surface); border: 1px solid var(--border);
        border-radius: 8px; padding: 1rem 1.2rem;
        transition: border-color .2s, transform .15s;
        display: flex; flex-direction: column; gap: .3rem; }
.card:hover { border-color: var(--accent); transform: translateY(-2px); text-decoration: none; }
.card .num { color: var(--muted); font-size: .75rem; }
.card-title { font-size: .95rem; font-weight: 600; color: var(--text); }
.card .stars { font-size: .85rem; margin-top: auto; }

.sekce { margin: 2.5rem 0; }
.sekce-header { display: flex; align-items: center; gap: .8rem;
                margin-bottom: 1rem; }
.sekce-icon { font-size: 1.6rem; line-height: 1; }
.sekce-info h2 { font-size: 1.15rem; margin: 0; }
.sekce-info p  { color: var(--muted); font-size: .85rem; margin: .15rem 0 0; }
.sekce-badge { margin-left: auto; background: var(--border);
               color: var(--muted); font-size: .75rem;
               padding: .2rem .6rem; border-radius: 999px; white-space: nowrap; }

.lekce-header { margin-bottom: 1.5rem; }
.lekce-header h1 { font-size: 1.8rem; margin-bottom: .5rem; }
.meta { color: var(--muted); font-size: .9rem; display: flex; gap: 1rem; }

.docstring { background: var(--surface); border-left: 3px solid var(--accent);
             padding: 1rem 1.2rem; border-radius: 0 6px 6px 0;
             margin-bottom: 1.5rem; white-space: pre-wrap;
             font-size: .92rem; color: var(--muted); }

pre.kod { background: var(--code-bg); border: 1px solid var(--border);
          border-radius: 8px; padding: 1.2rem; overflow-x: auto;
          font-family: 'Cascadia Code', 'Fira Code', monospace;
          font-size: .88rem; line-height: 1.5; }

.kw  { color: #ff7b72; }
.st  { color: #a5d6ff; }
.cm  { color: #8b949e; font-style: italic; }
.fn  { color: #d2a8ff; }
.nb  { color: #79c0ff; }
.nm  { color: #ffa657; }
.ky  { color: #ff7b72; }   /* YAML keys */
.ya  { color: #3fb950; }   /* YAML anchors / Dockerfile instructions */

.ulohy { background: var(--surface); border: 1px solid var(--border);
         border-radius: 8px; padding: 1rem 1.2rem; margin-top: 1.5rem; }
.ulohy h3 { margin-bottom: .6rem; color: var(--green); }
.ulohy li { margin-left: 1.2rem; margin-bottom: .5rem; }
.reseni-detail { margin-top: .3rem; }
.reseni-detail summary { color: var(--accent); cursor: pointer; font-size: .85rem; }
.reseni-detail summary:hover { text-decoration: underline; }
.reseni-detail code { display: block; margin-top: .4rem; background: var(--code-bg);
                      border: 1px solid var(--border); border-radius: 5px;
                      padding: .5rem .8rem; font-size: .85rem; white-space: pre-wrap; }

nav.zpet { margin-bottom: 1.5rem; }
footer { text-align: center; color: var(--muted); font-size: .8rem;
         padding: 2rem; border-top: 1px solid var(--border); margin-top: 3rem; }

html.light {
  --bg: #ffffff; --surface: #f6f8fa; --border: #d0d7de;
  --text: #1f2328; --muted: #636c76; --accent: #0969da;
  --green: #1a7f37; --yellow: #9a6700; --red: #d1242f;
  --code-bg: #f6f8fa;
}
html.light .kw  { color: #cf222e; }
html.light .st  { color: #0a3069; }
html.light .cm  { color: #6e7781; }
html.light .fn  { color: #6639ba; }
html.light .nb  { color: #0550ae; }
html.light .nm  { color: #953800; }
"""

# ══════════════════════════════════════════════════════════════
# Sekce
# ══════════════════════════════════════════════════════════════

SEKCE = [
    {
        "rozsah": range(1, 8),
        "nazev":  "Docker — základy",
        "ikona":  "🐳",
        "popis":  "Kontejnery, Dockerfile, images, volumes, Compose, registry",
        "barva":  "#58a6ff",
    },
    {
        "rozsah": range(8, 13),
        "nazev":  "Kubernetes — základy",
        "ikona":  "☸️",
        "popis":  "Cluster, Pod, Deployment, Service, ConfigMap, Secret",
        "barva":  "#3fb950",
    },
    {
        "rozsah": range(13, 16),
        "nazev":  "Kubernetes — produkce",
        "ikona":  "🚀",
        "popis":  "Ingress, Helm, kompletní deployment pipeline",
        "barva":  "#d2a8ff",
    },
]


def sekce_pro(cislo: int) -> str:
    for s in SEKCE:
        if cislo in s["rozsah"]:
            return s["nazev"]
    return "Ostatní"


# ══════════════════════════════════════════════════════════════
# Syntax highlighting — Python + YAML + Dockerfile + Shell
# ══════════════════════════════════════════════════════════════

PYTHON_KW = (
    r"\b(def|class|return|import|from|if|elif|else|for|while|"
    r"try|except|finally|with|as|pass|break|continue|yield|"
    r"lambda|and|or|not|in|is|True|False|None|async|await|"
    r"raise|del|global|nonlocal|assert|match|case)\b"
)
PYTHON_BUILTINS = (
    r"\b(print|input|len|range|type|isinstance|list|dict|set|"
    r"tuple|str|int|float|bool|open|super|property|staticmethod|"
    r"classmethod|enumerate|zip|map|filter|sorted|reversed|"
    r"min|max|sum|abs|round|hasattr|getattr|setattr|vars|"
    r"subprocess|Path|textwrap)\b"
)
DOCKERFILE_KW = (
    r"^(FROM|RUN|COPY|ADD|WORKDIR|ENV|EXPOSE|CMD|ENTRYPOINT|"
    r"ARG|USER|HEALTHCHECK|LABEL|VOLUME|STOPSIGNAL|SHELL|ONBUILD)"
    r"(?=\s)"
)


def sub_mimo_spany(vzor: str, nahrada: str, text: str, flags: int = 0) -> str:
    segmenty = re.split(r'(<span[^>]*>.*?</span>)', text, flags=re.DOTALL)
    vysledek = []
    for i, seg in enumerate(segmenty):
        if i % 2 == 0:
            vysledek.append(re.sub(vzor, nahrada, seg, flags=flags))
        else:
            vysledek.append(seg)
    return "".join(vysledek)


def zvyrazni(kod: str) -> str:
    escp = html.escape(kod)

    # 1. Komentare (#)
    escp = sub_mimo_spany(r"(#[^\n]*)", r'<span class="cm">\1</span>', escp)

    # 2. Trojite uvozovky (docstringy)
    Q3 = r'(&quot;&quot;&quot;.*?&quot;&quot;&quot;)'
    A3 = r"(&#x27;&#x27;&#x27;.*?&#x27;&#x27;&#x27;)"
    escp = sub_mimo_spany(Q3, r'<span class="st">\1</span>', escp, re.DOTALL)
    escp = sub_mimo_spany(A3, r'<span class="st">\1</span>', escp, re.DOTALL)

    # 3. Jednořádkové retezce
    Q1 = r'(&quot;[^&\n]*(?:&[^;\n]*;[^&\n]*)*&quot;)'
    A1 = r"(&#x27;[^&#\n]*(?:&#[^;\n]*;[^&#\n]*)*&#x27;)"
    escp = sub_mimo_spany(Q1, r'<span class="st">\1</span>', escp)
    escp = sub_mimo_spany(A1, r'<span class="st">\1</span>', escp)

    # 4. Cisla
    escp = sub_mimo_spany(
        r"\b(\d[\d_]*\.?\d*(?:[eE][+-]?\d+)?)\b",
        r'<span class="nm">\1</span>', escp
    )

    # 5. Dockerfile instrukce (zacinaji radek)
    escp = sub_mimo_spany(
        DOCKERFILE_KW,
        r'<span class="ya">\1</span>', escp,
        re.MULTILINE
    )

    # 6. Python builtins
    escp = sub_mimo_spany(PYTHON_BUILTINS, r'<span class="nb">\1</span>', escp)

    # 7. Python keywords
    escp = sub_mimo_spany(PYTHON_KW, r'<span class="kw">\1</span>', escp)

    # 8. def/class jmeno
    escp = re.sub(
        r'(<span class="kw">(?:def|class)</span>)\s+(\w+)',
        r'\1 <span class="fn">\2</span>', escp
    )

    return escp


def odstran_ulohy_z_kodu(kod: str) -> str:
    radky = kod.splitlines()
    vysledek = []
    preskakuj = False
    for radek in radky:
        stripped = radek.strip()
        if stripped.startswith("# TVOJE ULOA") or stripped.startswith("# TVOJE ULOHA"):
            preskakuj = True
        if not preskakuj:
            vysledek.append(radek)
    return "\n".join(vysledek).rstrip()


# ══════════════════════════════════════════════════════════════
# Generátory stránek
# ══════════════════════════════════════════════════════════════

def generuj_index(lekce: list[dict], vystup: Path) -> None:
    sekce_lekce: dict[str, list] = {}
    for l in lekce:
        sekce_lekce.setdefault(sekce_pro(l["cislo"]), []).append(l)

    bloky = ""
    for s in SEKCE:
        skupina = sekce_lekce.get(s["nazev"], [])
        if not skupina:
            continue

        karty = ""
        for l in skupina:
            karty += (
                f'    <a class="card" href="lekce/{l["slug"]}.html" data-slug="{l["slug"]}">\n'
                f'      <div class="num">Lekce {l["cislo"]:02d}</div>\n'
                f'      <div class="card-title">{html.escape(l["titul"])}</div>\n'
                f'      <div class="stars">{l["obtiznost"]}</div>\n'
                f'    </a>\n'
            )

        bloky += (
            f'<div class="sekce">\n'
            f'  <div class="sekce-header" style="border-left:3px solid {s["barva"]};padding-left:.8rem">\n'
            f'    <span class="sekce-icon">{s["ikona"]}</span>\n'
            f'    <div class="sekce-info">\n'
            f'      <h2>{html.escape(s["nazev"])}</h2>\n'
            f'      <p>{html.escape(s["popis"])}</p>\n'
            f'    </div>\n'
            f'    <span class="sekce-badge">{len(skupina)} lekcí</span>\n'
            f'  </div>\n'
            f'  <div class="grid">\n{karty}  </div>\n'
            f'</div>\n'
        )

    search_data = json.dumps([
        {"cislo": l["cislo"], "titul": l["titul"],
         "slug": l["slug"], "sekce": sekce_pro(l["cislo"])}
        for l in lekce
    ], ensure_ascii=False)

    stranky = f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Docker & Kubernetes — od nuly k hrdinovi</title>
  <style>{CSS}
.search-wrap {{ position:relative; margin:1.2rem 0; }}
#hledej {{ width:100%; padding:.65rem 1rem .65rem 2.5rem; background:var(--surface);
           border:1px solid var(--border); border-radius:8px; color:var(--text);
           font-size:1rem; outline:none; }}
#hledej:focus {{ border-color:var(--accent); }}
.search-icon {{ position:absolute; left:.8rem; top:50%; transform:translateY(-50%);
                color:var(--muted); pointer-events:none; }}
#vysledky {{ position:absolute; width:100%; background:var(--surface);
             border:1px solid var(--border); border-radius:8px; z-index:99;
             max-height:320px; overflow-y:auto; top:calc(100% + 4px); }}
#vysledky a {{ display:block; padding:.5rem 1rem; color:var(--text); border-bottom:1px solid var(--border); }}
#vysledky a:last-child {{ border-bottom:none; }}
#vysledky a:hover {{ background:var(--code-bg); text-decoration:none; }}
#vysledky .hit-sekce {{ font-size:.75rem; color:var(--muted); }}
#vysledky:empty {{ display:none; }}
.theme-btn {{ background:none; border:1px solid var(--border); color:var(--text);
              padding:.3rem .7rem; border-radius:6px; cursor:pointer; font-size:.85rem; }}
.theme-btn:hover {{ border-color:var(--accent); }}
.card.hotovo {{ border-color:var(--green); opacity:.7; }}
.card.hotovo::after {{ content:"✓"; position:absolute; top:.5rem; right:.7rem;
                       color:var(--green); font-weight:700; }}
.card {{ position:relative; }}
.progress-bar {{ height:4px; background:var(--border); border-radius:2px; margin:.5rem 0 1rem; }}
.progress-fill {{ height:100%; background:var(--green); border-radius:2px; transition:width .4s; }}
  </style>
</head>
<body>
<header>
  <h1>🐳 Docker &amp; ☸️ Kubernetes</h1>
  <div style="display:flex;gap:.7rem;align-items:center;margin-left:auto">
    <span class="badge">{len(lekce)} lekcí</span>
    <button class="theme-btn" onclick="toggleTheme()" title="Přepnout téma">☀️</button>
  </div>
</header>
<main>
  <p style="color:var(--muted);margin-top:1rem">
    Od prvního <code>docker run</code> po produkční Kubernetes cluster.
    Každá lekce je spustitelný Python skript — učíš se děláním.
  </p>
  <div class="search-wrap">
    <span class="search-icon">🔍</span>
    <input id="hledej" type="search" placeholder="Hledej lekci… (např. volume, deployment, ingress)" autocomplete="off">
    <div id="vysledky"></div>
  </div>
  <div class="progress-bar"><div class="progress-fill" id="progress-fill" style="width:0%"></div></div>
  <div id="progress-text" style="font-size:.8rem;color:var(--muted);margin-bottom:1rem"></div>
  {bloky}
</main>
<footer>Vygenerováno Pythonem · Docker &amp; Kubernetes kurz</footer>
<script>
const LEKCE = {search_data};
const hledej = document.getElementById("hledej");
const vysledky = document.getElementById("vysledky");

hledej.addEventListener("input", () => {{
  const q = hledej.value.trim().toLowerCase();
  vysledky.innerHTML = "";
  if (q.length < 2) return;
  const shody = LEKCE.filter(l =>
    l.titul.toLowerCase().includes(q) || l.sekce.toLowerCase().includes(q)
  ).slice(0, 8);
  shody.forEach(l => {{
    const a = document.createElement("a");
    a.href = "lekce/" + l.slug + ".html";
    a.innerHTML = `<strong>Lekce ${{String(l.cislo).padStart(2,"0")}}: ${{l.titul}}</strong>
      <div class="hit-sekce">${{l.sekce}}</div>`;
    vysledky.appendChild(a);
  }});
}});

document.addEventListener("click", e => {{
  if (!hledej.contains(e.target)) vysledky.innerHTML = "";
}});

const HOTOVO_KEY = "k8s_kurz_hotovo";
function getHotovo() {{ return JSON.parse(localStorage.getItem(HOTOVO_KEY) || "[]"); }}
function setHotovo(list) {{ localStorage.setItem(HOTOVO_KEY, JSON.stringify(list)); }}

function updateProgress() {{
  const hotovo = getHotovo();
  const total = {len(lekce)};
  const pct = Math.round(hotovo.length / total * 100);
  document.getElementById("progress-fill").style.width = pct + "%";
  document.getElementById("progress-text").textContent =
    hotovo.length > 0 ? `Dokončeno ${{hotovo.length}} z ${{total}} lekcí (${{pct}}%)` : "";
  document.querySelectorAll(".card[data-slug]").forEach(card => {{
    card.classList.toggle("hotovo", hotovo.includes(card.dataset.slug));
  }});
}}

document.querySelectorAll(".card[data-slug]").forEach(card => {{
  card.addEventListener("dblclick", e => {{
    e.preventDefault();
    const slug = card.dataset.slug;
    const hotovo = getHotovo();
    const idx = hotovo.indexOf(slug);
    if (idx === -1) hotovo.push(slug); else hotovo.splice(idx, 1);
    setHotovo(hotovo);
    updateProgress();
  }});
}});
updateProgress();

function toggleTheme() {{
  const isLight = document.documentElement.classList.toggle("light");
  localStorage.setItem("theme", isLight ? "light" : "dark");
  document.querySelector(".theme-btn").textContent = isLight ? "🌙" : "☀️";
}}
const savedTheme = localStorage.getItem("theme");
if (savedTheme === "light") {{
  document.documentElement.classList.add("light");
  document.querySelector(".theme-btn").textContent = "🌙";
}}
</script>
</body>
</html>"""

    vystup.write_text(stranky, encoding="utf-8")


def generuj_lekci(l: dict, vystup: Path, prev_l=None, next_l=None) -> None:
    doc_html = html.escape(
        textwrap.dedent(l["docstring"]).strip()
    ) if l["docstring"] else ""

    ulohy_html = ""
    if l["ulohy"]:
        items_html = ""
        for i, u in enumerate(l["ulohy"]):
            res = l["reseni"][i] if i < len(l["reseni"]) else ""
            reseni_html = (
                f'<details class="reseni-detail"><summary>Zobraz řešení</summary>'
                f'<code>{html.escape(res)}</code></details>'
            ) if res else ""
            items_html += f"<li>{html.escape(u)}{reseni_html}</li>\n"
        ulohy_html = f'<div class="ulohy"><h3>Tvoje úlohy 💪</h3><ul>{items_html}</ul></div>'

    kod_bez_uloh = odstran_ulohy_z_kodu(l["kod"])

    prev_html = (
        f'<a class="nav-btn" href="{prev_l["slug"]}.html">← {html.escape(prev_l["titul"])}</a>'
        if prev_l else '<span></span>'
    )
    next_html = (
        f'<a class="nav-btn" href="{next_l["slug"]}.html">{html.escape(next_l["titul"])} →</a>'
        if next_l else '<span></span>'
    )

    stranka = f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Lekce {l['cislo']:02d}: {html.escape(l['titul'])}</title>
  <style>{CSS}
.page-nav {{ display:flex; justify-content:space-between; margin:1.5rem 0; gap:1rem; }}
.nav-btn {{ background:var(--surface); border:1px solid var(--border);
            padding:.5rem 1rem; border-radius:6px; font-size:.9rem; }}
.nav-btn:hover {{ border-color:var(--accent); text-decoration:none; }}
.kod-wrap {{ position:relative; }}
.copy-btn {{ position:absolute; top:.6rem; right:.6rem; background:var(--border);
             border:none; color:var(--text); padding:.3rem .7rem; border-radius:5px;
             cursor:pointer; font-size:.8rem; opacity:.7; }}
.copy-btn:hover {{ opacity:1; }}
.theme-btn {{ background:none; border:1px solid var(--border); color:var(--text);
              padding:.3rem .7rem; border-radius:6px; cursor:pointer; font-size:.85rem; }}
  </style>
</head>
<body>
<header>
  <h1><a href="../index.html" style="color:inherit;text-decoration:none">🐳 Docker &amp; ☸️ Kubernetes</a></h1>
  <div style="display:flex;gap:.7rem;align-items:center;margin-left:auto">
    <a href="../index.html" style="font-size:.9rem">← Přehled</a>
    <button class="theme-btn" onclick="toggleTheme()" title="Přepnout téma">☀️</button>
  </div>
</header>
<main>
  <div class="lekce-header">
    <h1>Lekce {l['cislo']:02d}: {html.escape(l['titul'])}</h1>
    <div class="meta">
      <span>{l['soubor']}</span>
      <span>{l['obtiznost']}</span>
    </div>
  </div>
  {'<div class="docstring">' + doc_html + '</div>' if doc_html else ''}
  <div class="kod-wrap">
    <button class="copy-btn" onclick="kopiruj(this)">Kopírovat</button>
    <pre class="kod"><code>{zvyrazni(kod_bez_uloh)}</code></pre>
  </div>
  {ulohy_html}
  <div class="page-nav">{prev_html}{next_html}</div>
</main>
<footer>Vygenerováno Pythonem · Docker &amp; Kubernetes kurz</footer>
<script>
function kopiruj(btn) {{
  const kod = btn.nextElementSibling.textContent;
  navigator.clipboard.writeText(kod).then(() => {{
    btn.textContent = "Zkopírováno ✓";
    setTimeout(() => btn.textContent = "Kopírovat", 2000);
  }});
}}
function toggleTheme() {{
  const isLight = document.documentElement.classList.toggle("light");
  localStorage.setItem("theme", isLight ? "light" : "dark");
  document.querySelector(".theme-btn").textContent = isLight ? "🌙" : "☀️";
}}
const savedTheme = localStorage.getItem("theme");
if (savedTheme === "light") {{
  document.documentElement.classList.add("light");
  document.querySelector(".theme-btn").textContent = "🌙";
}}
</script>
</body>
</html>"""

    vystup.write_text(stranka, encoding="utf-8")


# ══════════════════════════════════════════════════════════════
# Sestavení webu
# ══════════════════════════════════════════════════════════════

def sestav_web():
    print("\n=== Sestavuji Docker & Kubernetes kurz web ===\n")

    web_dir   = zde / "web"
    lekce_dir = web_dir / "lekce"
    lekce_dir.mkdir(parents=True, exist_ok=True)

    soubory = sorted(zde.glob("[0-9][0-9]_*.py"))
    lekce   = [nacti_lekci(s) for s in soubory]
    print(f"Načteno {len(lekce)} lekcí.")

    generuj_index(lekce, web_dir / "index.html")
    print(f"  ✓ web/index.html")

    for stary in lekce_dir.glob("*.html"):
        cist = ascii_stem(stary.stem) + stary.suffix
        if cist != stary.name:
            stary.unlink()

    for i, l in enumerate(lekce):
        cil = lekce_dir / f"{l['slug']}.html"
        prev_l = lekce[i - 1] if i > 0 else None
        next_l = lekce[i + 1] if i < len(lekce) - 1 else None
        generuj_lekci(l, cil, prev_l, next_l)
        print(f"  ✓ web/lekce/{l['slug']}.html")

    print(f"\nHotovo! Otevři:")
    print(f"  {web_dir / 'index.html'}")
    print(f"\nNebo spusť lokální server:")
    print(f"  cd {web_dir} && python3 -m http.server 8080")
    print(f"  Pak jdi na: http://localhost:8080")


if __name__ == "__main__":
    sestav_web()
