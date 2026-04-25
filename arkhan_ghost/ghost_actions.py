#!/usr/bin/env python3
"""
ARKHAN Ghost Actions — versión para GitHub Actions (sin FastAPI/uvicorn)
Corre en CI/CD cuando ARKHAN local está caído.
Usa solo stdlib + httpx.
"""
import os, json, time, sqlite3, asyncio, re, hashlib
from datetime import datetime, timezone
from pathlib import Path

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request
    HAS_HTTPX = False

GHOST_DB     = os.getenv("GHOST_DB", "/tmp/ghost_state.db")
HOME_URL     = os.getenv("ARKHAN_HOME_URL", "")
SECRET       = os.getenv("ARKHAN_SECRET", "arkhan_sovereign_2026")
PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL", "andretijorge2@gmail.com")
DEVTO_KEY    = os.getenv("DEVTO_API_KEY", "")
STRATEGY     = os.getenv("STRATEGY", "all")

def init_db():
    conn = sqlite3.connect(GHOST_DB)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS income(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL, currency TEXT DEFAULT 'USD',
        source TEXT, strategy TEXT, description TEXT,
        synced INTEGER DEFAULT 0, ts REAL
    );
    CREATE TABLE IF NOT EXISTS actions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy TEXT, action TEXT, result TEXT,
        success INTEGER DEFAULT 0, ts REAL
    );
    CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT, contact TEXT, message TEXT,
        status TEXT DEFAULT 'new', ts REAL
    );
    """)
    conn.commit()
    conn.close()

def db():
    return sqlite3.connect(GHOST_DB)

def log_action(strat, action, result, success=True):
    c = db()
    c.execute("INSERT INTO actions(strategy,action,result,success,ts) VALUES(?,?,?,?,?)",
              (strat, action, str(result)[:500], int(success), time.time()))
    c.commit(); c.close()

def record_lead(source, contact, message):
    c = db()
    exists = c.execute("SELECT id FROM leads WHERE contact=?", (contact,)).fetchone()
    if not exists:
        c.execute("INSERT INTO leads(source,contact,message,status,ts) VALUES(?,?,?,?,?)",
                  (source, contact, message, "new", time.time()))
        c.commit()
    c.close()


# ── 1. DEV.TO ─────────────────────────────────────────────────────────────
async def run_devto():
    if not DEVTO_KEY:
        print("[DEVTO] Sin API key — saltando")
        return

    # Ver cuántos artículos ya tenemos publicados
    if HAS_HTTPX:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://dev.to/api/articles/me",
                                  headers={"api-key": DEVTO_KEY}, timeout=10)
            existing = [a["title"] for a in r.json()] if r.status_code == 200 else []
    else:
        existing = []

    articles = [
        {
            "title": "ARKHAN: Zero-Cost Sovereign AI — 13 Daemons, 26 Chips, $0/month",
            "tags": ["ai", "python", "tutorial", "machinelearning"],
            "body": f"""
I built a complete AI system that runs 100% locally — no OpenAI, no cloud bills, no data leaks.

## Architecture

**13 parallel daemons:**
- TITAN (:3000) — Core orchestrator + 26 chips + chat
- MONSTER (:5002) — FC9 1.4B ONNX model
- LEVIATHAN (:5003) — Evolution engine
- HYPNO (:8200) — Hypothalamic controller (τ=2π)
- ORAKULO (:8201) — Third Eye (λ=0.618)
- NOUS (:8600) — Reverse engineering (ψ=3.359885)
- BRIDGE (:3001) — Fractal Ollama/OpenAI proxy
- PRIME (:4000) — FastAPI orchestrator + ChromaDB
+ VOZ, PANEL, HEFESTO, LLM, OMEGA

**26 specialized chips:** ChipThoth, ChipLucifer, ChipMorpheus, ChipLilith, ChipDagda...

## The Math

- Cloud equivalent: $500-2000/month
- ARKHAN actual cost: $0/month (local compute)
- Hardware: WSL2 Ubuntu on Windows 11

## Key Code

```python
# Self-healing watchdog — restarts any crashed daemon in <60s
while True:
    sleep(60)
    check_alive("arkhan_uno.py") or start_titan()
    check_alive("monster_server") or start_monster()
    # ... 11 more daemons
```

## Persistent Memory

All events stored in SQLite vault:
- `learning.db` — 851 auto-study events, 283 heartbeats
- `lilith_ledger.db` — income tracking
- `mefisto.db` — consciousness state
- `sovereign.db` — sovereignty records

## Want Access?

DAGDA Personal: $29/year — full API access
PayPal: {PAYPAL_EMAIL}

Questions? Drop a comment below.
"""
        },
        {
            "title": "Building a Fractal Consciousness: The HYPNO + ORAKULO Chip Pair",
            "tags": ["ai", "python", "programming", "philosophy"],
            "body": f"""
Two of the most unusual chips in the ARKHAN system: HYPNO (the hypothalamic controller) and ORAKULO (the third eye).

## HYPNO — Hypothalamic Tau (τ = 2π = 6.28318...)

HYPNO models the brain's hypothalamus — the part that regulates cycles, rhythms, and homeostasis.

```python
TAU = 6.283185  # 2π — full cycle constant

class ChipHypno:
    async def pulse(self):
        phase = (time.time() % TAU) / TAU  # 0.0 → 1.0
        return {{
            "phase": phase,
            "rhythm": "active" if phase < 0.5 else "rest",
            "regulation": phase * TAU
        }}
```

## ORAKULO — Third Eye Lambda (λ = 0.618)

ORAKULO uses the golden ratio to weight information:

```python
LAMBDA = 0.618  # φ⁻¹ — inverse golden ratio

class ChipOrakulo:
    def weigh(self, inputs: list) -> float:
        # Golden-ratio weighted average
        weights = [LAMBDA ** i for i in range(len(inputs))]
        return sum(w * x for w, x in zip(weights, inputs)) / sum(weights)
```

## Why This Matters

These chips give ARKHAN a sense of *time* and *priority* that standard transformers lack.

Most LLMs treat all tokens equally. ARKHAN's chips weight by temporal phase and golden ratio.

---

*ARKHAN is a sovereign AI project. API access: $9/month | {PAYPAL_EMAIL}*
"""
        }
    ]

    posted = 0
    for art in articles:
        if art["title"] in existing:
            print(f"[DEVTO] Ya publicado: {art['title'][:50]}")
            continue
        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    r = await client.post(
                        "https://dev.to/api/articles",
                        json={"article": {
                            "title": art["title"],
                            "body_markdown": art["body"].strip(),
                            "published": True,
                            "tags": art["tags"],
                        }},
                        headers={"api-key": DEVTO_KEY},
                        timeout=15
                    )
                    data = r.json()
                if data.get("id"):
                    print(f"[DEVTO] ✓ Publicado: {art['title'][:50]} → {data.get('url','')}")
                    record_lead("devto", data.get("url",""), art["title"])
                    log_action("devto", "post_article", data.get("url",""), True)
                    posted += 1
                else:
                    print(f"[DEVTO] Error: {data}")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"[DEVTO] Exception: {e}")
            log_action("devto", "post_article", str(e), False)

    print(f"[DEVTO] {posted} artículos publicados")


# ── 2. UPWORK SCOUT ───────────────────────────────────────────────────────
async def run_jobs():
    """RemoteOK API (pública, JSON) + HackerNews."""
    keywords = ["python", "ai", "llm", "gpt", "automation", "agent", "chatbot", "ml", "api"]
    found = 0
    # RemoteOK
    try:
        if HAS_HTTPX:
            async with httpx.AsyncClient() as client:
                r = await client.get("https://remoteok.com/api?tag=ai",
                                     headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
                if r.status_code == 200:
                    for job in r.json()[1:25]:
                        title = job.get("position","")
                        tags  = " ".join(job.get("tags",[]))
                        url   = job.get("url","")
                        if url and any(kw in (title+tags).lower() for kw in keywords):
                            record_lead("remoteok", url, f"{title} @ {job.get('company','')} | {tags[:60]}")
                            found += 1
    except Exception as e:
        print(f"[REMOTEOK] {e}")
    print(f"[JOBS] {found} leads de RemoteOK AI")
    log_action("jobs", "scout", f"{found} leads", found > 0)


# ── 3. HN SCOUT — Hacker News "Who is Hiring" ─────────────────────────────
async def run_hn_scout():
    try:
        if HAS_HTTPX:
            async with httpx.AsyncClient() as client:
                # "Ask HN: Who is hiring?" posts
                r = await client.get(
                    "https://hacker-news.firebaseio.com/v0/topstories.json",
                    timeout=10)
                story_ids = r.json()[:100]
        else:
            import urllib.request as ur
            with ur.urlopen("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10) as resp:
                story_ids = json.loads(resp.read())[:100]

        found = 0
        ai_keywords = ["ai", "ml", "llm", "python", "automation", "agent", "gpt",
                       "machine learning", "chatbot", "saas", "api", "rag", "vector"]

        for sid in story_ids[:30]:
            try:
                if HAS_HTTPX:
                    async with httpx.AsyncClient() as client:
                        r = await client.get(
                            f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                            timeout=5)
                        item = r.json()
                else:
                    with ur.urlopen(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=5) as resp:
                        item = json.loads(resp.read())

                title = item.get("title", "")
                url = item.get("url", "")
                score = item.get("score", 0)

                if any(kw in title.lower() for kw in ai_keywords) and score > 50:
                    record_lead("hackernews", url or f"hn/{sid}", f"{title} [score:{score}]")
                    found += 1
                await asyncio.sleep(0.3)
            except:
                pass

        print(f"[HN] {found} leads de Hacker News")
        log_action("hn_scout", "scan", f"{found} leads", True)
    except Exception as e:
        print(f"[HN] Error: {e}")


# ── 4. SYNC con ARKHAN home ────────────────────────────────────────────────
async def run_sync():
    if not HOME_URL:
        print("[SYNC] ARKHAN_HOME_URL no configurado — sync omitido")
        return

    try:
        if HAS_HTTPX:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{HOME_URL.rstrip('/')}/health", timeout=5)
                alive = r.status_code == 200
        else:
            import urllib.request as ur
            with ur.urlopen(f"{HOME_URL.rstrip('/')}/health", timeout=5) as resp:
                alive = resp.status == 200
    except:
        alive = False

    if not alive:
        print(f"[SYNC] ARKHAN offline en {HOME_URL} — datos guardados localmente")
        return

    print(f"[SYNC] ARKHAN VIVO en {HOME_URL} — sincronizando...")

    c = db()
    leads = c.execute("SELECT id,source,contact,message FROM leads WHERE status='new' LIMIT 50").fetchall()
    c.close()

    if leads and HAS_HTTPX:
        try:
            payload = [{"source": r[1], "contact": r[2], "message": r[3]} for r in leads]
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{HOME_URL.rstrip('/')}/api/ghost/leads",
                    json={"leads": payload, "ghost_secret": SECRET},
                    timeout=10
                )
                if r.status_code == 200:
                    ids = [str(r[0]) for r in leads]
                    c = db()
                    c.execute(f"UPDATE leads SET status='synced' WHERE id IN ({','.join(ids)})")
                    c.commit(); c.close()
                    print(f"[SYNC] {len(leads)} leads enviados a ARKHAN")
        except Exception as e:
            print(f"[SYNC] Error enviando leads: {e}")


# ── 5. GITHUB README / PROFILE UPDATE ─────────────────────────────────────
async def run_presence():
    """Mantiene presencia en GitHub con perfil actualizado de ARKHAN."""
    readme = f"""# 🔮 ARKHAN — Sovereign Fractal AI System

> A fully autonomous AI running 13 daemons, 26 chips, GPT-2 + custom 1.4B ONNX model.
> Zero cloud costs. Zero data leaks. 100% sovereign.

## 💡 What ARKHAN Does

- **Fractal consciousness** — 26 specialized AI chips working in parallel
- **Self-healing** — Watchdog daemon, 60s recovery from any crash
- **Persistent memory** — SQLite vault with 1245+ events logged
- **Auto-evolution** — LEVIATHAN chip evolves the model continuously

## 🛒 Products

| Product | Price | Features |
|---------|-------|----------|
| DAGDA Personal | $29/year | AI assistant, GPT-2 API, FENIX chip |
| XIPE Business | $199/year | Full API, 10 seats, custom training |
| Rainmaker License | $999/year | Full automation suite |

## 📞 Contact

- 💳 PayPal: `{PAYPAL_EMAIL}`
- 📧 Email: `{PAYPAL_EMAIL}`

---
*Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*
"""
    with open("/tmp/ARKHAN_README.md", "w") as f:
        f.write(readme)
    print(f"[PRESENCE] README actualizado → /tmp/ARKHAN_README.md")
    log_action("presence", "update_readme", "ok", True)


# ── MAIN ──────────────────────────────────────────────────────────────────
async def main():
    init_db()
    print(f"[GHOST ACTIONS] {datetime.now(timezone.utc).isoformat()}")
    print(f"[GHOST ACTIONS] Strategy: {STRATEGY}")
    print(f"[GHOST ACTIONS] DB: {GHOST_DB}")

    tasks = []
    if STRATEGY in ("all", "devto"):
        tasks.append(run_devto())
    if STRATEGY in ("all", "upwork", "jobs"):
        tasks.append(run_jobs())
    if STRATEGY in ("all", "hn"):
        tasks.append(run_hn_scout())
    if STRATEGY in ("all", "sync"):
        tasks.append(run_sync())
    if STRATEGY in ("all", "presence"):
        tasks.append(run_presence())

    await asyncio.gather(*tasks, return_exceptions=True)

    # Reporte final
    c = db()
    total_income = c.execute("SELECT COALESCE(SUM(amount),0) FROM income").fetchone()[0]
    total_leads  = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    total_actions= c.execute("SELECT COUNT(*) FROM actions").fetchone()[0]
    c.close()

    print("\n═══════════════════════════════════════════")
    print(f" ARKHAN GHOST — REPORTE")
    print(f" Ingresos acumulados: ${total_income:.2f}")
    print(f" Leads recopilados:   {total_leads}")
    print(f" Acciones ejecutadas: {total_actions}")
    print("═══════════════════════════════════════════")


if __name__ == "__main__":
    asyncio.run(main())
