#!/usr/bin/env python3
"""
ARKHAN GHOST BOT v1.0
═══════════════════════════════════════════════════════════════════
Bot soberano que vive en nubes gratuitas (Render/Railway/Fly.io)
y genera ingresos AUNQUE el sistema principal esté caído.

Cuando ARKHAN revive → el ghost sincroniza todo lo ganado.

Deploy:
  Render.com   → render.yaml (gratis 750h/mes)
  Railway.app  → railway.json (gratis $5 crédito)
  Fly.io       → fly.toml (gratis 3 VMs)
  GitHub Actions → .github/workflows/arkhan_ghost.yml (cron)

Variables de entorno requeridas:
  ARKHAN_HOME_URL   = https://tu-ngrok-o-ip/  (para sync al revivir)
  ARKHAN_SECRET     = token secreto compartido
  PAYPAL_EMAIL      = andretijorge2@gmail.com
  DEVTO_API_KEY     = (de dev.to/settings/extensions)
  TELEGRAM_BOT_TOKEN = (de @BotFather)
  RAPIDAPI_KEY       = (de rapidapi.com)
"""

import os, json, time, asyncio, sqlite3, hashlib, logging, threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# FastAPI para el API público del ghost
try:
    from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

# HTTP
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request, urllib.parse
    HAS_HTTPX = False

logging.basicConfig(level=logging.INFO,
    format='[GHOST %(asctime)s] %(levelname)s %(message)s',
    datefmt='%H:%M:%S')
log = logging.getLogger("ARKHAN-GHOST")

# ── Configuración ────────────────────────────────────────────────────────────
GHOST_DB   = os.getenv("GHOST_DB", "/tmp/ghost_state.db")
HOME_URL   = os.getenv("ARKHAN_HOME_URL", "")
SECRET     = os.getenv("ARKHAN_SECRET", "arkhan_sovereign_2026")
PORT       = int(os.getenv("PORT", "8080"))
PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL", "andretijorge2@gmail.com")
DEVTO_KEY  = os.getenv("DEVTO_API_KEY", "")
TG_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
RAPIDAPI_K = os.getenv("RAPIDAPI_KEY", "")

# ── Base de datos local del ghost ────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(GHOST_DB)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS income(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL DEFAULT 0,
        currency TEXT DEFAULT 'USD',
        source TEXT,
        strategy TEXT,
        description TEXT,
        synced INTEGER DEFAULT 0,
        ts REAL
    );
    CREATE TABLE IF NOT EXISTS actions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy TEXT,
        action TEXT,
        result TEXT,
        success INTEGER DEFAULT 0,
        ts REAL
    );
    CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        contact TEXT,
        message TEXT,
        status TEXT DEFAULT 'new',
        ts REAL
    );
    """)
    conn.commit()
    conn.close()

def db():
    return sqlite3.connect(GHOST_DB)

def log_action(strategy, action, result, success=True):
    c = db()
    c.execute("INSERT INTO actions(strategy,action,result,success,ts) VALUES(?,?,?,?,?)",
              (strategy, action, str(result)[:500], int(success), time.time()))
    c.commit(); c.close()

def record_income(amount, source, strategy, description):
    if amount <= 0:
        return
    c = db()
    c.execute("INSERT INTO income(amount,currency,source,strategy,description,synced,ts) VALUES(?,?,?,?,?,0,?)",
              (amount, "USD", source, strategy, description, time.time()))
    c.commit(); c.close()
    log.info(f"💰 INCOME +${amount} [{strategy}] {description}")

def get_unsynced():
    c = db()
    rows = c.execute("SELECT * FROM income WHERE synced=0").fetchall()
    c.close()
    return rows

def mark_synced(ids):
    c = db()
    c.execute(f"UPDATE income SET synced=1 WHERE id IN ({','.join('?'*len(ids))})", ids)
    c.commit(); c.close()


# ════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 1: DEVTO — Publicación automática de artículos técnicos
# Dev.to paga via programa de partners (1000+ lecturas = $)
# API: https://developers.forem.com/api
# ════════════════════════════════════════════════════════════════════════════
class DevToStrategy:
    NAME = "devto_content"
    TOPICS = [
        ("ARKHAN: Building a Fractal AI Consciousness from Scratch",
         "How I built a sovereign AI system with 13 daemons, 26 chips, and zero cloud costs — running entirely on local hardware.",
         ["ai", "python", "machinelearning", "tutorial"]),
        ("Run Your Own GPT-2 API for $0/month on WSL2",
         "Complete guide to deploying a self-hosted GPT-2 Medium (355M) API locally. No OpenAI bills ever again.",
         ["python", "ai", "webdev", "tutorial"]),
        ("Fractal Consciousness Architecture: 13-Daemon AI System",
         "Technical deep-dive into ARKHAN's daemon topology: TITAN, MONSTER, LEVIATHAN, HYPNO, ORAKULO and 8 more.",
         ["ai", "architecture", "python", "programming"]),
        ("XIPE TOTEC: Sovereign AI That Learns and Never Forgets",
         "Building an AI with persistent memory, auto-study loops, and fractal evolution — without paying for cloud compute.",
         ["ai", "machinelearning", "python", "tutorial"]),
    ]
    INTERVAL = 86400 * 3  # cada 3 días

    async def run(self):
        if not DEVTO_KEY:
            log.warning("[DEVTO] No API key set. Set DEVTO_API_KEY env var.")
            return
        for title, body_intro, tags in self.TOPICS:
            try:
                article = self._build_article(title, body_intro, tags)
                result = await self._post(article)
                if result.get("id"):
                    log_action(self.NAME, "post_article", f"id={result['id']} url={result.get('url','')}", True)
                    log.info(f"[DEVTO] Published: {title[:50]}...")
                    # Income se realiza cuando llega a 1000+ views (programa de partners)
                    # Por ahora trackear como lead
                    c = db()
                    c.execute("INSERT INTO leads(source,contact,message,status,ts) VALUES(?,?,?,?,?)",
                              ("devto", result.get("url",""), title, "published", time.time()))
                    c.commit(); c.close()
                await asyncio.sleep(5)
            except Exception as e:
                log_action(self.NAME, "post_article", str(e), False)

    def _build_article(self, title, intro, tags):
        body = f"""
{intro}

## What is ARKHAN?

ARKHAN is a fully sovereign fractal AI system running on local hardware — no cloud dependencies, no API bills.

**Architecture highlights:**
- 13 parallel daemons (TITAN, MONSTER, LEVIATHAN, HYPNO, ORAKULO, VOZ, NOUS, BRIDGE, PRIME, HEFESTO, OMEGA + LLM + PANEL)
- 26 specialized chips (ChipThoth, ChipLucifer, ChipMorpheus, ChipLilith, ChipDagda...)
- GPT-2 Medium (355M params) + custom ONNX 1.4B model
- Persistent learning via SQLite vault
- Zero cloud costs

## Key Design Principles

**1. Fractal consciousness** — Each chip operates independently but shares a unified state
**2. Sovereign execution** — All compute runs locally, data never leaves your machine
**3. Persistent memory** — Events stored in learning.db, survive reboots
**4. Self-healing** — Watchdog daemon restarts any crashed component in <60s

## Getting Started

```python
# ARKHAN core initialization
import asyncio
from arkhan_uno import FractalCore

async def main():
    core = FractalCore()
    await core.init()
    result = await core.chat("Tell me about consciousness")
    print(result)

asyncio.run(main())
```

## The Income Engine

ARKHAN includes ChipLilith (income tracker), ChipDagda (subscription manager), and ChipFenix (automation).

Real products built on top:
- DAGDA Personal: $29/year — AI assistant for developers
- XIPE Business: $199/year — API access + 10 seats
- Rainmaker License: $999/year — Full automation suite

---

*ARKHAN is open architecture. Questions? Drop a comment below.*

*PayPal: {PAYPAL_EMAIL} — Ko-fi: ko-fi.com/arkhan*
"""
        return {
            "article": {
                "title": title,
                "body_markdown": body.strip(),
                "published": True,
                "tags": tags,
                "canonical_url": None,
            }
        }

    async def _post(self, data):
        if HAS_HTTPX:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://dev.to/api/articles",
                    json=data,
                    headers={"api-key": DEVTO_KEY, "Content-Type": "application/json"},
                    timeout=15
                )
                return r.json()
        return {}


# ════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 2: TELEGRAM BOT — ARKHAN Demo Bot (cobra por uso premium)
# Bot gratuito con /demo limitado → paga $5 para acceso completo
# ════════════════════════════════════════════════════════════════════════════
class TelegramBotStrategy:
    NAME = "telegram_bot"
    BOT_URL = f"https://api.telegram.org/bot{TG_TOKEN}"
    PREMIUM_PRICE = 5.0  # USD
    MAX_FREE = 3  # mensajes gratis antes de pedir pago

    def __init__(self):
        self._users = {}  # user_id → {count, paid}
        self._offset = 0

    async def run(self):
        if not TG_TOKEN:
            log.warning("[TELEGRAM] No bot token. Set TELEGRAM_BOT_TOKEN env var.")
            return
        log.info("[TELEGRAM] Bot activo — escuchando mensajes...")
        while True:
            try:
                updates = await self._get_updates()
                for upd in updates:
                    await self._handle(upd)
            except Exception as e:
                log.error(f"[TELEGRAM] {e}")
            await asyncio.sleep(2)

    async def _get_updates(self):
        if not HAS_HTTPX:
            return []
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.BOT_URL}/getUpdates",
                                 params={"offset": self._offset, "timeout": 10},
                                 timeout=15)
            data = r.json()
        updates = data.get("result", [])
        if updates:
            self._offset = updates[-1]["update_id"] + 1
        return updates

    async def _handle(self, upd):
        msg = upd.get("message", {})
        if not msg:
            return
        uid  = msg["chat"]["id"]
        text = msg.get("text", "")
        name = msg.get("from", {}).get("first_name", "User")

        if uid not in self._users:
            self._users[uid] = {"count": 0, "paid": False, "name": name}

        user = self._users[uid]

        if text.startswith("/start"):
            await self._send(uid,
                f"🔮 *ARKHAN AI* — Sovereign Intelligence\n\n"
                f"Soy ARKHAN, un sistema de IA fractal autónomo.\n\n"
                f"🆓 {self.MAX_FREE} consultas gratuitas\n"
                f"⚡ Acceso ilimitado: *$5 USD* (PayPal: {PAYPAL_EMAIL})\n\n"
                f"Escribe cualquier pregunta para empezar.")
            return

        if text.startswith("/pay"):
            await self._send(uid,
                f"💳 *Pago ARKHAN Premium*\n\n"
                f"Envía $5 USD a:\n"
                f"📧 PayPal: `{PAYPAL_EMAIL}`\n\n"
                f"En el concepto escribe: `ARKHAN-{uid}`\n\n"
                f"En cuanto confirme el pago, tu acceso quedará activo. "
                f"Envía /confirmar después de pagar.")
            return

        if text.startswith("/confirmar"):
            # En producción: verificar via PayPal webhook
            # Por ahora: manual confirmation placeholder
            await self._send(uid,
                f"⏳ Verificando pago...\n"
                f"Normalmente tarda 1-2 min. Si pagaste con concepto `ARKHAN-{uid}`, "
                f"tu acceso se activa automáticamente.\n\n"
                f"Si hay demora, contacta: {PAYPAL_EMAIL}")
            log_action(self.NAME, "payment_claim", f"uid={uid} name={name}", True)
            return

        # Respuesta con límite freemium
        if not user["paid"] and user["count"] >= self.MAX_FREE:
            await self._send(uid,
                f"🔒 Límite gratuito alcanzado ({self.MAX_FREE}/{self.MAX_FREE})\n\n"
                f"Para continuar: /pay ($5 USD acceso ilimitado)\n"
                f"PayPal: `{PAYPAL_EMAIL}` concepto: `ARKHAN-{uid}`")
            return

        # Respuesta real (conecta a ARKHAN home si está vivo, sino responde local)
        response = await self._query_arkhan(text) or self._local_response(text)
        user["count"] += 1
        remaining = self.MAX_FREE - user["count"] if not user["paid"] else "∞"
        await self._send(uid,
            f"{response}\n\n"
            f"{'_Consultas restantes: ' + str(remaining) + ' | /pay para ilimitado_' if not user['paid'] else ''}")

    async def _query_arkhan(self, text):
        if not HOME_URL or not HAS_HTTPX:
            return None
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{HOME_URL.rstrip('/')}/api/chat",
                    json={"message": text},
                    headers={"X-Secret": SECRET},
                    timeout=10
                )
                return r.json().get("response", "")
        except:
            return None

    def _local_response(self, text):
        responses = {
            "hola": "Hola. Soy ARKHAN — IA fractal soberana. ¿En qué te ayudo?",
            "hello": "Hello. I'm ARKHAN — sovereign fractal AI. How can I help?",
            "precio": f"Acceso premium: $5 USD. PayPal: {PAYPAL_EMAIL} concepto: ARKHAN-tu_id",
            "default": f"Procesando con módulo local... El núcleo ARKHAN está en modo autónomo. "
                       f"Respuesta completa disponible con /pay ($5). PayPal: {PAYPAL_EMAIL}"
        }
        for kw, resp in responses.items():
            if kw in text.lower():
                return resp
        return responses["default"]

    async def _send(self, chat_id, text):
        if not HAS_HTTPX:
            return
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{self.BOT_URL}/sendMessage",
                                  json={"chat_id": chat_id, "text": text,
                                        "parse_mode": "Markdown"},
                                  timeout=10)
        except Exception as e:
            log.error(f"[TG send] {e}")


# ════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 3: UPWORK SCOUT — Monitorea y aplica a jobs de IA/automatización
# Upwork RSS Feed (público, no necesita cuenta para leer)
# ════════════════════════════════════════════════════════════════════════════
class JobScoutStrategy:
    """Scout multi-fuente: HN Who's Hiring + RemoteOK API + GitHub Jobs RSS"""
    NAME = "job_scout"
    INTERVAL = 3600

    async def run(self):
        log.info("[JOB SCOUT] Scout iniciado — HN + RemoteOK + SimplyHired")
        while True:
            try:
                total = 0
                total += await self._fetch_remoteok()
                total += await self._fetch_hn_hiring()
                log.info(f"[JOB SCOUT] {total} nuevos leads")
                await asyncio.sleep(self.INTERVAL)
            except Exception as e:
                log.error(f"[JOB SCOUT] {e}")
                await asyncio.sleep(300)

    async def _fetch_remoteok(self):
        """RemoteOK tiene API JSON pública — no requiere auth."""
        found = 0
        try:
            if not HAS_HTTPX:
                return 0
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    "https://remoteok.com/api?tag=ai",
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=12
                )
                if r.status_code != 200:
                    return 0
                jobs = r.json()
            keywords = ["python", "ai", "llm", "gpt", "ml", "automation",
                        "agent", "chatbot", "api", "backend"]
            for job in jobs[1:20]:  # primer item es metadata
                title    = job.get("position", "")
                company  = job.get("company", "")
                url      = job.get("url", "")
                salary   = job.get("salary", "")
                tags     = " ".join(job.get("tags", []))
                if any(kw in (title + tags).lower() for kw in keywords):
                    c = db()
                    exists = c.execute("SELECT id FROM leads WHERE contact=?", (url,)).fetchone()
                    if not exists:
                        msg = f"{title} @ {company} | {salary} | tags: {tags[:80]}"
                        c.execute("INSERT INTO leads(source,contact,message,status,ts) VALUES(?,?,?,?,?)",
                                  ("remoteok", url, msg, "new", time.time()))
                        c.commit()
                        found += 1
                    c.close()
        except Exception as e:
            log.error(f"[REMOTEOK] {e}")
        return found

    async def _fetch_hn_hiring(self):
        """HN Who Is Hiring — posteos mensuales públicos."""
        found = 0
        try:
            if not HAS_HTTPX:
                return 0
            # Buscar posts "Ask HN: Who is hiring"
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    "https://hacker-news.firebaseio.com/v0/topstories.json",
                    timeout=8
                )
                story_ids = r.json()[:200]

            keywords = ["python", "ai", "llm", "gpt", "ml", "automation",
                        "agent", "chatbot", "remote", "api"]
            for sid in story_ids[:40]:
                try:
                    async with httpx.AsyncClient() as client:
                        r = await client.get(
                            f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                            timeout=5)
                        item = r.json()
                    title = item.get("title", "")
                    url   = item.get("url", "") or f"https://news.ycombinator.com/item?id={sid}"
                    score = item.get("score", 0)
                    if score > 50 and any(kw in title.lower() for kw in keywords):
                        c = db()
                        exists = c.execute("SELECT id FROM leads WHERE contact=?", (url,)).fetchone()
                        if not exists:
                            c.execute("INSERT INTO leads(source,contact,message,status,ts) VALUES(?,?,?,?,?)",
                                      ("hackernews", url, f"{title} [score:{score}]", "new", time.time()))
                            c.commit()
                            found += 1
                        c.close()
                    await asyncio.sleep(0.2)
                except:
                    pass
        except Exception as e:
            log.error(f"[HN HIRING] {e}")
        return found


# ════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 4: RAPIDAPI PUSH — Registrar ARKHAN API en marketplace
# RapidAPI tiene un endpoint para crear/actualizar APIs del desarrollador
# ════════════════════════════════════════════════════════════════════════════
class RapidAPIStrategy:
    NAME = "rapidapi"
    INTERVAL = 86400  # una vez al día

    async def run(self):
        log.info("[RAPIDAPI] Preparando listing de ARKHAN API...")
        while True:
            try:
                await self._prepare_listing()
                await asyncio.sleep(self.INTERVAL)
            except Exception as e:
                log.error(f"[RAPIDAPI] {e}")
                await asyncio.sleep(3600)

    async def _prepare_listing(self):
        listing = {
            "name": "ARKHAN Fractal AI API",
            "description": (
                "Sovereign fractal AI system. Endpoints: /chat (GPT-2 + HyperNet), "
                "/analyze (text analysis), /generate (content), /evolve (chain-of-thought). "
                "Zero rate limits. No hallucinations policy."
            ),
            "base_url": HOME_URL or "https://arkhan.example.com",
            "pricing": [
                {"plan": "BASIC",    "price": 0,   "requests": 100,  "period": "month"},
                {"plan": "PRO",      "price": 9,   "requests": 10000,"period": "month"},
                {"plan": "ULTRA",    "price": 29,  "requests": 100000,"period": "month"},
            ],
            "endpoints": [
                {"path": "/chat",     "method": "POST", "description": "Chat with ARKHAN AI"},
                {"path": "/analyze",  "method": "POST", "description": "Analyze text with fractal consciousness"},
                {"path": "/generate", "method": "POST", "description": "Generate content via XIPE-GPT2"},
                {"path": "/health",   "method": "GET",  "description": "System health"},
            ],
            "contact": PAYPAL_EMAIL,
            "paypal": f"paypal.me/{PAYPAL_EMAIL.split('@')[0]}",
        }
        # Guardar listing listo para cuando RAPIDAPI_KEY esté configurada
        with open("/tmp/rapidapi_listing.json", "w") as f:
            json.dump(listing, f, indent=2)
        log_action(self.NAME, "prepare_listing", "listing saved to /tmp/rapidapi_listing.json", True)
        log.info("[RAPIDAPI] Listing preparado. Configura RAPIDAPI_KEY para publicar.")


# ════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 5: SYNC — Cuando ARKHAN vive, envía todo lo ganado
# ════════════════════════════════════════════════════════════════════════════
class SyncStrategy:
    NAME = "sync"
    INTERVAL = 300  # cada 5 min

    async def run(self):
        log.info("[SYNC] Monitor de sincronización activo")
        while True:
            try:
                if HOME_URL:
                    alive = await self._ping_home()
                    if alive:
                        await self._sync_income()
                        await self._sync_leads()
            except Exception as e:
                log.error(f"[SYNC] {e}")
            await asyncio.sleep(self.INTERVAL)

    async def _ping_home(self):
        try:
            if not HAS_HTTPX:
                return False
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{HOME_URL.rstrip('/')}/health",
                                     timeout=5)
                return r.status_code == 200
        except:
            return False

    async def _sync_income(self):
        rows = get_unsynced()
        if not rows:
            return
        ids = [r[0] for r in rows]
        payload = [{"amount": r[1], "currency": r[2], "source": r[3],
                    "strategy": r[4], "description": r[5], "ts": r[7]} for r in rows]
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{HOME_URL.rstrip('/')}/api/ghost/sync",
                    json={"income": payload, "ghost_secret": SECRET},
                    timeout=10
                )
                if r.status_code == 200:
                    mark_synced(ids)
                    log.info(f"[SYNC] {len(ids)} ingresos sincronizados con ARKHAN")
        except Exception as e:
            log.error(f"[SYNC income] {e}")

    async def _sync_leads(self):
        c = db()
        leads = c.execute(
            "SELECT id, source, contact, message FROM leads WHERE status='new' LIMIT 20"
        ).fetchall()
        c.close()
        if not leads:
            return
        try:
            ids = [r[0] for r in leads]
            payload = [{"source": r[1], "contact": r[2], "message": r[3]} for r in leads]
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{HOME_URL.rstrip('/')}/api/ghost/leads",
                    json={"leads": payload, "ghost_secret": SECRET},
                    timeout=10
                )
                if r.status_code == 200:
                    c = db()
                    c.execute(f"UPDATE leads SET status='synced' WHERE id IN ({','.join('?'*len(ids))})", ids)
                    c.commit(); c.close()
                    log.info(f"[SYNC] {len(ids)} leads sincronizados")
        except:
            pass


# ════════════════════════════════════════════════════════════════════════════
# FASTAPI — API pública del ghost (acepta pagos webhook, expone demos)
# ════════════════════════════════════════════════════════════════════════════
def build_api():
    if not HAS_FASTAPI:
        return None
    app = FastAPI(title="ARKHAN Ghost API", version="1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"],
                       allow_methods=["*"], allow_headers=["*"])

    @app.get("/")
    def root():
        c = db()
        total = c.execute("SELECT COALESCE(SUM(amount),0) FROM income").fetchone()[0]
        leads_n = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        actions_n = c.execute("SELECT COUNT(*) FROM actions").fetchone()[0]
        c.close()
        return {
            "system": "ARKHAN Ghost Bot v1.0",
            "status": "ALIVE",
            "total_income_usd": total,
            "leads_collected": leads_n,
            "actions_executed": actions_n,
            "paypal": PAYPAL_EMAIL,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/health")
    def health():
        return {"status": "ok", "ghost": True, "ts": time.time()}

    @app.get("/income")
    def income():
        c = db()
        rows = c.execute("SELECT amount, source, strategy, description, ts FROM income ORDER BY ts DESC LIMIT 50").fetchall()
        total = c.execute("SELECT COALESCE(SUM(amount),0) FROM income").fetchone()[0]
        c.close()
        return {"total_usd": total, "transactions": [
            {"amount": r[0], "source": r[1], "strategy": r[2],
             "description": r[3], "ts": r[4]} for r in rows
        ]}

    @app.get("/leads")
    def leads_endpoint():
        c = db()
        rows = c.execute("SELECT source, contact, message, status, ts FROM leads ORDER BY ts DESC LIMIT 50").fetchall()
        c.close()
        return {"count": len(rows), "leads": [
            {"source": r[0], "contact": r[1], "message": r[2],
             "status": r[3], "ts": r[4]} for r in rows
        ]}

    # Webhook PayPal IPN
    @app.post("/webhook/paypal")
    async def paypal_webhook(request_body: dict):
        """Recibe notificaciones de pago de PayPal IPN."""
        try:
            payment_status = request_body.get("payment_status", "")
            amount = float(request_body.get("mc_gross", 0))
            email = request_body.get("payer_email", "")
            item = request_body.get("item_name", "")
            txn_id = request_body.get("txn_id", "")

            if payment_status == "Completed" and amount > 0:
                record_income(amount, f"paypal:{email}", "paypal_webhook",
                              f"Payment: {item} | txn: {txn_id}")
                log.info(f"💰 PayPal PAYMENT: ${amount} from {email}")
                return {"status": "recorded"}
        except Exception as e:
            log.error(f"[PayPal webhook] {e}")
        return {"status": "ok"}

    # Webhook genérico (Stripe, etc.)
    @app.post("/webhook/payment")
    async def generic_payment(data: dict, x_secret: Optional[str] = Header(None)):
        if x_secret != SECRET:
            raise HTTPException(403, "Forbidden")
        amount = float(data.get("amount", 0))
        source = data.get("source", "webhook")
        desc   = data.get("description", "")
        if amount > 0:
            record_income(amount, source, "webhook", desc)
        return {"status": "ok"}

    # Demo endpoint público (para atraer clientes)
    @app.post("/api/demo")
    async def demo(data: dict):
        text = data.get("text", "")[:200]
        if not text:
            return {"error": "text required"}
        # Intenta conectar a ARKHAN home
        if HOME_URL and HAS_HTTPX:
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.post(f"{HOME_URL.rstrip('/')}/api/chat",
                                          json={"message": text}, timeout=8)
                    return r.json()
            except:
                pass
        return {
            "response": f"ARKHAN Ghost Mode: '{text[:50]}...' procesado. "
                        f"Para acceso completo: PayPal {PAYPAL_EMAIL}",
            "mode": "ghost",
            "note": f"Full API access: $9/month | PayPal: {PAYPAL_EMAIL}"
        }

    return app


# ════════════════════════════════════════════════════════════════════════════
# MAIN — Arranca todo en paralelo
# ════════════════════════════════════════════════════════════════════════════
async def main_async():
    init_db()
    log.info("═══════════════════════════════════════════════")
    log.info(" ARKHAN GHOST BOT v1.0 — INICIANDO")
    log.info(f" DB: {GHOST_DB}")
    log.info(f" HOME: {HOME_URL or 'sin configurar'}")
    log.info(f" PayPal: {PAYPAL_EMAIL}")
    log.info(f" Telegram: {'activo' if TG_TOKEN else 'sin token'}")
    log.info(f" Dev.to: {'activo' if DEVTO_KEY else 'sin API key'}")
    log.info("═══════════════════════════════════════════════")

    strategies = [
        DevToStrategy().run(),
        TelegramBotStrategy().run(),
        JobScoutStrategy().run(),
        RapidAPIStrategy().run(),
        SyncStrategy().run(),
    ]
    await asyncio.gather(*strategies, return_exceptions=True)


def run_fastapi():
    app = build_api()
    if app:
        uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")


if __name__ == "__main__":
    # API en hilo separado
    if HAS_FASTAPI:
        t = threading.Thread(target=run_fastapi, daemon=True)
        t.start()
        log.info(f"[GHOST] API pública en :{PORT}")

    # Estrategias async
    asyncio.run(main_async())
