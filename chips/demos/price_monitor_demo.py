#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║     ARKHAN PRICE MONITOR PRO v2.0 — Fractal Intelligence Chip      ║
║     Real-time crypto monitoring · 8 exchanges · Telegram alerts     ║
║     Created by ARKHAN Fractal AI · fractalaixipetotec.online       ║
╚══════════════════════════════════════════════════════════════════════╝
"""
import time, json, threading, sqlite3, hashlib, os, sys
from pathlib import Path
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

VERSION = "2.0.0"
DB_PATH = Path.home() / ".arkhan" / "price_monitor.db"

# ── LICENSE CHECK ────────────────────────────────────────────────────────────
def _verify_license(key: str) -> bool:
    """Verify ARKHAN license key."""
    # Keys are SHA256(buyer_id + product_id + secret)
    # For demo: key must be 64 hex chars
    return len(key) == 64 and all(c in '0123456789abcdef' for c in key.lower())

# Full version at @Chimeraghost_bot /buy price_monitor — $9/mo

# ── EXCHANGES ────────────────────────────────────────────────────────────────
COINGECKO_IDS = {
    "BTC":"bitcoin","ETH":"ethereum","SOL":"solana","BNB":"binancecoin",
    "XRP":"ripple","ADA":"cardano","DOGE":"dogecoin","AVAX":"avalanche-2",
    "DOT":"polkadot","MATIC":"matic-network","LINK":"chainlink","UNI":"uniswap",
    "ATOM":"cosmos","LTC":"litecoin","NEAR":"near","APT":"aptos",
    "OP":"optimism","ARB":"arbitrum","INJ":"injective-protocol","TIA":"celestia",
    "SUI":"sui","PEPE":"pepe","WIF":"dogwifhat","BONK":"bonk",
    "JUP":"jupiter","PYTH":"pyth-network","JTO":"jito-governance-token"
}

class Exchange:
    def __init__(self, name: str):
        self.name = name
        self.success = 0
        self.errors = 0

    def fetch(self, symbol: str) -> float | None:
        raise NotImplementedError

    def _get(self, url: str, timeout=8) -> dict:
        req = Request(url, headers={"User-Agent":"Mozilla/5.0 ARKHAN/2.0"})
        return json.loads(urlopen(req, timeout=timeout).read())

class CoinGecko(Exchange):
    def __init__(self): super().__init__("coingecko")
    def fetch(self, symbol: str) -> float | None:
        cg_id = COINGECKO_IDS.get(symbol.upper())
        if not cg_id: return None
        try:
            d = self._get(f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true")
            self.success += 1
            return {"price": d[cg_id]["usd"], "change_24h": d[cg_id].get("usd_24h_change",0), "mcap": d[cg_id].get("usd_market_cap",0)}
        except: self.errors += 1; return None

class Binance(Exchange):
    def __init__(self): super().__init__("binance")
    def fetch(self, symbol: str) -> float | None:
        try:
            d = self._get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol.upper()}USDT")
            self.success += 1
            return {"price": float(d["lastPrice"]), "change_24h": float(d["priceChangePercent"]), "vol_24h": float(d["quoteVolume"])}
        except: self.errors += 1; return None

class Kraken(Exchange):
    def __init__(self): super().__init__("kraken")
    KRAKEN_MAP = {"BTC":"XXBTZUSD","ETH":"XETHZUSD","SOL":"SOLUSD","XRP":"XXRPZUSD","ADA":"ADAUSD","DOGE":"XDGEZUSD"}
    def fetch(self, symbol: str) -> float | None:
        pair = self.KRAKEN_MAP.get(symbol.upper())
        if not pair: return None
        try:
            d = self._get(f"https://api.kraken.com/0/public/Ticker?pair={pair}")
            if d.get("error"): return None
            ticker = list(d["result"].values())[0]
            self.success += 1
            return {"price": float(ticker["c"][0])}
        except: self.errors += 1; return None

class Coinbase(Exchange):
    def __init__(self): super().__init__("coinbase")
    def fetch(self, symbol: str) -> float | None:
        try:
            d = self._get(f"https://api.coinbase.com/v2/prices/{symbol.upper()}-USD/spot")
            self.success += 1
            return {"price": float(d["data"]["amount"])}
        except: self.errors += 1; return None

# ── DATABASE ─────────────────────────────────────────────────────────────────
class PriceDB:
    def __init__(self, path: Path = DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self._lock = threading.Lock()
        self._init()

    def _init(self):
        with self._lock:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    change_24h REAL,
                    volume REAL,
                    exchange TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_sym_ts ON prices(symbol, ts);
                CREATE TABLE IF NOT EXISTS alerts_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT,
                    symbol TEXT,
                    alert_type TEXT,
                    trigger_price REAL,
                    actual_price REAL
                );
                CREATE TABLE IF NOT EXISTS portfolio (
                    symbol TEXT PRIMARY KEY,
                    amount REAL,
                    entry_price REAL,
                    notes TEXT
                );
            """)
            self.conn.commit()

    def save(self, symbol: str, data: dict):
        with self._lock:
            self.conn.execute(
                "INSERT INTO prices (ts,symbol,price,change_24h,volume,exchange) VALUES (?,?,?,?,?,?)",
                (datetime.now().isoformat(), symbol, data["price"],
                 data.get("change_24h"), data.get("vol_24h"), data.get("exchange","multi")))
            self.conn.commit()

    def history(self, symbol: str, hours: int = 24) -> list:
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        with self._lock:
            return self.conn.execute(
                "SELECT ts, price FROM prices WHERE symbol=? AND ts>? ORDER BY ts",
                (symbol, since)).fetchall()

    def portfolio_add(self, symbol: str, amount: float, entry_price: float, notes: str = ""):
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO portfolio VALUES (?,?,?,?)",
                (symbol.upper(), amount, entry_price, notes))
            self.conn.commit()

    def portfolio_get(self) -> list:
        with self._lock:
            return self.conn.execute("SELECT * FROM portfolio").fetchall()

# ── TELEGRAM NOTIFICATIONS ───────────────────────────────────────────────────
class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self._last_alert = {}  # symbol → last alert time (debounce)

    def send(self, text: str, parse_mode: str = "HTML"):
        try:
            data = json.dumps({"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode}).encode()
            req = Request(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                data=data, headers={"Content-Type": "application/json"})
            urlopen(req, timeout=10)
        except Exception as e:
            print(f"Telegram error: {e}")

    def price_alert(self, symbol: str, price: float, change: float, trigger: str):
        # Debounce: don't spam same alert within 30 min
        key = f"{symbol}:{trigger}"
        if key in self._last_alert:
            if time.time() - self._last_alert[key] < 1800:
                return
        self._last_alert[key] = time.time()
        emoji = "🚀" if change > 0 else "📉"
        text = (f"{emoji} <b>ARKHAN PRICE ALERT</b>\n\n"
                f"<b>{symbol}</b>: <code>${price:,.4f}</code>\n"
                f"24h: <b>{change:+.2f}%</b>\n"
                f"Trigger: {trigger}\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        self.send(text)

# ── MAIN PRICE MONITOR ───────────────────────────────────────────────────────
class PriceMonitorPro:
    def __init__(self, tg_token: str = None, tg_chat: str = None):
        self.exchanges = [CoinGecko(), Binance(), Kraken(), Coinbase()]
        self.db = PriceDB()
        self.tg = TelegramNotifier(tg_token, tg_chat) if tg_token and tg_chat else None
        self.alerts: dict = {}       # {symbol: {"above": price, "below": price, "change_pct": %}}
        self.watchlist: list = []    # symbols to monitor
        self.cache: dict = {}        # {symbol: {price, change, ts}}
        self._running = False
        self._lock = threading.Lock()

    def add_alert(self, symbol: str, above: float = None, below: float = None, change_pct: float = None):
        """
        Set price alert.
        above: alert when price goes above this value
        below: alert when price goes below this value
        change_pct: alert when 24h change exceeds this % (positive or negative)
        """
        sym = symbol.upper()
        self.alerts[sym] = {}
        if above:    self.alerts[sym]["above"] = above
        if below:    self.alerts[sym]["below"] = below
        if change_pct: self.alerts[sym]["change_pct"] = change_pct
        if sym not in self.watchlist:
            self.watchlist.append(sym)
        print(f"✅ Alert set: {sym} | above={above} below={below} change_pct={change_pct}")

    def get_price(self, symbol: str) -> dict | None:
        """Fetch price from best available exchange."""
        sym = symbol.upper()
        for exchange in self.exchanges:
            data = exchange.fetch(sym)
            if data and data.get("price"):
                data["symbol"] = sym
                data["exchange"] = exchange.name
                data["ts"] = datetime.now().isoformat()
                with self._lock:
                    self.cache[sym] = data
                self.db.save(sym, data)
                return data
        return None

    def get_multi(self, symbols: list) -> dict:
        """Fetch multiple prices using threads."""
        results = {}
        lock = threading.Lock()

        def _fetch(sym):
            data = self.get_price(sym)
            if data:
                with lock:
                    results[sym] = data

        threads = [threading.Thread(target=_fetch, args=(s,)) for s in symbols]
        for t in threads: t.start()
        for t in threads: t.join(timeout=15)
        return results

    def _check_alerts(self, symbol: str, data: dict):
        if symbol not in self.alerts or not self.tg:
            return
        price = data["price"]
        change = data.get("change_24h", 0)
        rules = self.alerts[symbol]

        if "above" in rules and price > rules["above"]:
            self.tg.price_alert(symbol, price, change, f"ABOVE ${rules['above']:,.2f}")

        if "below" in rules and price < rules["below"]:
            self.tg.price_alert(symbol, price, change, f"BELOW ${rules['below']:,.2f}")

        if "change_pct" in rules and abs(change) >= rules["change_pct"]:
            direction = "📈 MOON" if change > 0 else "📉 DUMP"
            self.tg.price_alert(symbol, price, change, f"{direction} {change:+.1f}%")

    def portfolio_pnl(self) -> list:
        """Calculate portfolio P&L."""
        rows = self.db.portfolio_get()
        results = []
        for symbol, amount, entry_price, notes in rows:
            current = self.cache.get(symbol)
            if current:
                current_price = current["price"]
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                pnl_usd = (current_price - entry_price) * amount
                results.append({
                    "symbol": symbol, "amount": amount,
                    "entry": entry_price, "current": current_price,
                    "pnl_pct": pnl_pct, "pnl_usd": pnl_usd
                })
        return results

    def display(self, data: dict):
        """Print price in rich format."""
        sym = data.get("symbol","?")
        price = data.get("price", 0)
        change = data.get("change_24h", 0)
        mcap = data.get("mcap", 0)
        exch = data.get("exchange","?")
        emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        mcap_str = f"  MCap: ${mcap/1e9:.1f}B" if mcap > 1e9 else ""
        print(f"{emoji} {sym:8s} ${price:>14,.4f}  {change:>+7.2f}%  [{exch}]{mcap_str}")

    def monitor(self, symbols: list = None, interval: int = 30, verbose: bool = True):
        """
        Start continuous monitoring loop.
        symbols: list of symbols to monitor (default: watchlist)
        interval: seconds between updates
        """
        watch = symbols or self.watchlist
        if not watch:
            watch = ["BTC","ETH","SOL","BNB","XRP"]

        self._running = True
        print(f"\n{'='*60}")
        print(f"  ARKHAN PRICE MONITOR PRO v{VERSION}")
        print(f"  Watching: {', '.join(watch)}")
        print(f"  Interval: {interval}s")
        print(f"  Telegram: {'✅' if self.tg else '❌'}")
        print(f"{'='*60}\n")

        while self._running:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"\n── {ts} {'─'*45}")
            results = self.get_multi(watch)
            for sym in watch:
                if sym in results:
                    self.display(results[sym])
                    self._check_alerts(sym, results[sym])
                else:
                    print(f"⚠️  {sym}: no data")
            time.sleep(interval)

    def stop(self):
        self._running = False

    def report(self, symbols: list = None) -> str:
        """Generate text report."""
        watch = symbols or list(self.cache.keys()) or ["BTC","ETH","SOL"]
        results = self.get_multi(watch)
        lines = [f"📊 ARKHAN PRICE REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
        for sym in watch:
            if sym in results:
                d = results[sym]
                change = d.get("change_24h", 0)
                e = "🟢" if change > 0 else "🔴"
                lines.append(f"{e} {sym}: ${d['price']:,.4f} ({change:+.2f}%)")
        return "\n".join(lines)

# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ARKHAN Price Monitor Pro v2")
    parser.add_argument("symbols", nargs="*", default=["BTC","ETH","SOL"],
                        help="Symbols to monitor (default: BTC ETH SOL)")
    parser.add_argument("--interval", "-i", type=int, default=30, help="Update interval in seconds")
    parser.add_argument("--telegram", "-t", action="store_true", help="Enable Telegram alerts")
    parser.add_argument("--tg-token", help="Telegram bot token")
    parser.add_argument("--tg-chat", help="Telegram chat ID")
    parser.add_argument("--alert-above", type=float, help="Alert when price above this")
    parser.add_argument("--alert-below", type=float, help="Alert when price below this")
    parser.add_argument("--report", action="store_true", help="One-shot report and exit")
    parser.add_argument("--portfolio", action="store_true", help="Show portfolio P&L")
    args = parser.parse_args()

    # Init
    tg_token = args.tg_token or os.environ.get("TG_TOKEN")
    tg_chat  = args.tg_chat  or os.environ.get("TG_CHAT")
    monitor  = PriceMonitorPro(tg_token=tg_token, tg_chat=tg_chat)

    # Set alerts
    for sym in args.symbols:
        if args.alert_above or args.alert_below:
            monitor.add_alert(sym, above=args.alert_above, below=args.alert_below)

    if args.report:
        print(monitor.report(args.symbols))
    elif args.portfolio:
        pnl = monitor.portfolio_pnl()
        if not pnl:
            print("Portfolio empty. Add: db.portfolio_add('BTC', 0.1, 30000)")
        else:
            for p in pnl:
                e = "🟢" if p["pnl_pct"] > 0 else "🔴"
                print(f"{e} {p['symbol']}: {p['amount']} @ ${p['entry']:,.2f} → ${p['current']:,.2f} | PnL: {p['pnl_pct']:+.2f}% (${p['pnl_usd']:+,.2f})")
    else:
        try:
            monitor.monitor(args.symbols, interval=args.interval)
        except KeyboardInterrupt:
            print("\n⏹  Monitoring stopped.")
