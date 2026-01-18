"""
Trading Memory Service
======================
Logs trades, P&L, and portfolio snapshots to Unk's memory system.
Syncs to LoreDB (SQLite), BigQuery, and Firestore for triple redundancy.

Who Visions LLC - AI with Dav3
"""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Load env variables for credentials
load_dotenv()

logger = logging.getLogger(__name__)

# BigQuery imports (optional)
try:
    from google.cloud import bigquery
    BQ_AVAILABLE = True
except ImportError:
    BQ_AVAILABLE = False
    bigquery = None

# Firestore imports (optional)
try:
    from google.cloud import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    firestore = None

# Notion imports (optional)
try:
    from notion_client import Client as NotionClient
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    NotionClient = None

# Database path
TRADES_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trades.sqlite")


class TradingMemory:
    """
    Central service for logging trading events to Unk's memory.
    
    Features:
    - Local SQLite for fast access
    - BigQuery sync for analytics
    - Firestore sync for RAG/vector search
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.db_path = TRADES_DB_PATH
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "unk-app-480102")
        self.bq_dataset = "dav1d_memory"
        self.bq_table = "trades"
        self.firestore_collection = "unk_trades"
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        # Initialize BigQuery client
        self.bq_client = None
        if BQ_AVAILABLE:
            try:
                self.bq_client = bigquery.Client(project=self.project_id)
                self._ensure_bq_table()
                logger.info("[TradingMemory] BigQuery connected: %s.%s", 
                           self.bq_dataset, self.bq_table)
            except Exception as e:
                logger.warning("[TradingMemory] BigQuery init failed: %s", e)
        
        # Initialize Firestore client
        self.fs_client = None
        if FIRESTORE_AVAILABLE:
            try:
                self.fs_client = firestore.Client(project=self.project_id)
                logger.info("[TradingMemory] Firestore connected")
            except Exception as e:
                logger.warning("[TradingMemory] Firestore init failed: %s", e)
        
        # Initialize Notion client
        self.notion_client = None
        self.notion_trade_db = os.getenv("NOTION_TRADE_LOG_DB_ID")
        self.notion_holdings_db = os.getenv("NOTION_HOLDINGS_DB_ID")
        self.notion_portfolio_db = os.getenv("NOTION_PORTFOLIO_DB_ID")
        
        notion_token = os.getenv("NOTION_OBSERVATORY_SECRET")
        if NOTION_AVAILABLE and notion_token:
            try:
                self.notion_client = NotionClient(auth=notion_token)
                logger.info("[TradingMemory] Notion connected")
            except Exception as e:
                logger.warning("[TradingMemory] Notion init failed: %s", e)
        
        self._initialized = True
        logger.info("[TradingMemory] Initialized (BQ=%s, FS=%s, Notion=%s)", 
                   self.bq_client is not None, self.fs_client is not None, self.notion_client is not None)
    
    def _init_db(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total_value REAL NOT NULL,
                pnl REAL,
                strategy TEXT,
                reason TEXT,
                synced_bq INTEGER DEFAULT 0,
                synced_fs INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                total_value REAL NOT NULL,
                buying_power REAL NOT NULL,
                holdings_json TEXT NOT NULL,
                synced_bq INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_timestamp 
            ON trades(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_symbol 
            ON trades(symbol, timestamp DESC)
        """)
        
        conn.commit()
        conn.close()
        logger.debug("[TradingMemory] SQLite initialized: %s", self.db_path)
    
    def _ensure_bq_table(self):
        """Ensure BigQuery table exists."""
        if not self.bq_client:
            return
            
        table_id = f"{self.project_id}.{self.bq_dataset}.{self.bq_table}"
        
        schema = [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("side", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("quantity", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("price", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("total_value", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("pnl", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("strategy", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("reason", "STRING", mode="NULLABLE"),
        ]
        
        table = bigquery.Table(table_id, schema=schema)
        
        try:
            self.bq_client.get_table(table_id)
            logger.debug("[TradingMemory] BQ table exists: %s", table_id)
        except Exception:
            try:
                self.bq_client.create_table(table)
                logger.info("[TradingMemory] Created BQ table: %s", table_id)
            except Exception as e:
                logger.warning("[TradingMemory] BQ table creation failed: %s", e)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LOGGING METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def log_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        pnl: Optional[float] = None,
        strategy: Optional[str] = None,
        reason: Optional[str] = None
    ) -> str:
        """
        Log a trade execution.
        
        Args:
            symbol: Trading pair (e.g., "BTC-USD")
            side: "buy" or "sell"
            quantity: Amount traded
            price: Execution price
            pnl: Realized P&L (for sells)
            strategy: Strategy name that triggered trade
            reason: AI reasoning for the decision
            
        Returns:
            Trade ID
        """
        trade_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        total_value = quantity * price
        
        # 1. Insert into SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trades 
            (id, timestamp, symbol, side, quantity, price, total_value, pnl, strategy, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (trade_id, timestamp, symbol, side, quantity, price, total_value, 
              pnl, strategy, reason))
        conn.commit()
        conn.close()
        
        logger.info("[TradingMemory] Logged trade: %s %s %.6f %s @ $%.2f",
                   trade_id[:8], side.upper(), quantity, symbol, price)
        
        # 2. Sync to BigQuery (async-safe)
        self._sync_trade_to_bq(trade_id, timestamp, symbol, side, quantity, 
                               price, total_value, pnl, strategy, reason)
        
        # 3. Sync to Firestore
        self._sync_trade_to_firestore(trade_id, timestamp, symbol, side, quantity,
                                      price, total_value, pnl, strategy, reason)
        
        # 4. Sync to Notion
        self._sync_trade_to_notion(trade_id, timestamp, symbol, side, quantity,
                                  price, total_value, pnl, strategy, reason)
        
        return trade_id
    
    def _sync_trade_to_bq(self, trade_id, timestamp, symbol, side, quantity,
                          price, total_value, pnl, strategy, reason):
        """Sync trade to BigQuery."""
        if not self.bq_client:
            return
            
        try:
            table_id = f"{self.project_id}.{self.bq_dataset}.{self.bq_table}"
            rows = [{
                "id": trade_id,
                "timestamp": timestamp,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "total_value": total_value,
                "pnl": pnl,
                "strategy": strategy,
                "reason": reason,
            }]
            errors = self.bq_client.insert_rows_json(table_id, rows)
            if errors:
                logger.warning("[TradingMemory] BQ insert errors: %s", errors)
            else:
                # Mark as synced
                conn = sqlite3.connect(self.db_path)
                conn.execute("UPDATE trades SET synced_bq = 1 WHERE id = ?", (trade_id,))
                conn.commit()
                conn.close()
        except Exception as e:
            logger.warning("[TradingMemory] BQ sync failed: %s", e)
    
    def _sync_trade_to_firestore(self, trade_id, timestamp, symbol, side, quantity,
                                  price, total_value, pnl, strategy, reason):
        """Sync trade to Firestore for RAG."""
        if not self.fs_client:
            return
            
        try:
            doc_ref = self.fs_client.collection(self.firestore_collection).document(trade_id)
            doc_ref.set({
                "id": trade_id,
                "timestamp": timestamp,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "total_value": total_value,
                "pnl": pnl,
                "strategy": strategy,
                "reason": reason,
                "content": f"{side.upper()} {quantity:.6f} {symbol} @ ${price:.2f}"
            })
            # Mark as synced
            conn = sqlite3.connect(self.db_path)
            conn.execute("UPDATE trades SET synced_fs = 1 WHERE id = ?", (trade_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("[TradingMemory] Firestore sync failed: %s", e)
    
    def _sync_trade_to_notion(self, trade_id, timestamp, symbol, side, quantity,
                              price, total_value, pnl, strategy, reason):
        """Sync trade to Notion Trade Log."""
        if not self.notion_client or not self.notion_trade_db:
            return
            
        try:
            # Map common symbols to asset types
            asset_type = "Crypto"
            if any(s in symbol for s in ["SPY", "QQQ", "AAPL", "TSLA"]):
                asset_type = "Stock"

            properties = {
                "Trade ID": {"title": [{"text": {"content": trade_id}}]},
                "Trade Type": {"select": {"name": side.capitalize()}},
                "Symbol": {"rich_text": [{"text": {"content": symbol}}]},
                "Asset Type": {"select": {"name": asset_type}},
                "Quantity": {"number": quantity},
                "Price Per Unit": {"number": price},
                "Total Value": {"number": total_value},
                "Date": {"date": {"start": timestamp}},
                "Platform": {"select": {"name": "Robinhood"}},
                "Strategy": {"select": {"name": strategy or "DCA"}}
            }
            if pnl is not None:
                properties["Realized P&L $"] = {"number": pnl}
            
            # Simple metadata-based context
            if reason:
                properties["Notes"] = {"rich_text": [{"text": {"content": reason[:2000]}}]}
                
            self.notion_client.pages.create(
                parent={"database_id": self.notion_trade_db},
                properties=properties
            )
            logger.info("[TradingMemory] Synced trade %s to Notion", trade_id[:8])
        except Exception as e:
            logger.warning("[TradingMemory] Notion trade sync failed: %s", e)
    
    def log_portfolio_snapshot(
        self,
        holdings: Dict[str, Dict],
        buying_power: float,
        total_value: float
    ) -> str:
        """
        Log current portfolio state.
        
        Args:
            holdings: Dict of symbol -> {quantity, value, pnl_percent}
            buying_power: Available cash
            total_value: Total portfolio value
            
        Returns:
            Snapshot ID
        """
        snapshot_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO portfolio_snapshots 
            (id, timestamp, total_value, buying_power, holdings_json)
            VALUES (?, ?, ?, ?, ?)
        """, (snapshot_id, timestamp, total_value, buying_power, json.dumps(holdings)))
        conn.commit()
        conn.close()
        
        # 2. Sync to Notion
        self._sync_snapshot_to_notion(snapshot_id, timestamp, total_value, buying_power)
        self._sync_holdings_to_notion(holdings)
        
        return snapshot_id

    def _sync_holdings_to_notion(self, holdings: Dict[str, Dict]):
        """Update Notion Current Holdings database."""
        if not self.notion_client or not self.notion_holdings_db:
            return
            
        for symbol, data in holdings.items():
            try:
                # Use search as query is problematic with this client version
                search_res = self.notion_client.search(
                    query=symbol,
                    filter={"property": "object", "value": "page"}
                ).get("results", [])
                
                # Filter for the correct database and matching symbol
                query = [
                    r for r in search_res 
                    if r.get("parent", {}).get("database_id", "").replace("-", "") == self.notion_holdings_db.replace("-", "")
                ]
                
                properties = {
                    "Quantity": {"number": data.get("quantity", 0)},
                    "Total Value": {"number": data.get("value", 0)},
                    "P&L %": {"number": data.get("pnl_percent", 0) / 100.0 if "pnl_percent" in data else 0},
                    "Last Updated": {"date": {"start": datetime.utcnow().isoformat() + "Z"}}
                }
                
                if query:
                    # Update existing page
                    page_id = query[0]["id"]
                    self.notion_client.pages.update(page_id=page_id, properties=properties)
                else:
                    # Create new page
                    properties.update({
                        "Asset Name": {"title": [{"text": {"content": symbol}}]},
                        "Symbol": {"rich_text": [{"text": {"content": symbol}}]},
                        "Asset Type": {"select": {"name": "Crypto"}},
                        "Platform": {"select": {"name": "Robinhood"}}
                    })
                    self.notion_client.pages.create(
                        parent={"database_id": self.notion_holdings_db},
                        properties=properties
                    )
            except Exception as e:
                logger.warning("[TradingMemory] Notion holdings sync failed for %s: %s", symbol, e)

    def _sync_snapshot_to_notion(self, snapshot_id, timestamp, total_value, buying_power):
        """Sync portfolio snapshot to Notion."""
        if not self.notion_client or not self.notion_portfolio_db:
            return
            
        try:
            properties = {
                "Snapshot Date": {"title": [{"text": {"content": timestamp[:10]}}]},
                "Date": {"date": {"start": timestamp}},
                "Total Value": {"number": total_value},
                "Cash": {"number": buying_power}
            }
            self.notion_client.pages.create(
                parent={"database_id": self.notion_portfolio_db},
                properties=properties
            )
            logger.info("[TradingMemory] Synced snapshot to Notion")
        except Exception as e:
            logger.warning("[TradingMemory] Notion snapshot sync failed: %s", e)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RETRIEVAL METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_recent_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most recent trades."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM trades 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_trades_by_symbol(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trades for a specific symbol."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM trades 
            WHERE symbol = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (symbol, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_pnl_summary(self, period: str = "24h") -> Dict[str, Any]:
        """
        Calculate P&L for a time period.
        
        Args:
            period: "24h", "7d", "30d", or "all"
            
        Returns:
            Dict with total_pnl, trade_count, win_rate, etc.
        """
        # Calculate cutoff time
        now = datetime.utcnow()
        if period == "24h":
            cutoff = now - timedelta(hours=24)
        elif period == "7d":
            cutoff = now - timedelta(days=7)
        elif period == "30d":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = datetime(2000, 1, 1)
        
        cutoff_str = cutoff.isoformat() + "Z"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get trades in period
        cursor.execute("""
            SELECT side, quantity, price, total_value, pnl 
            FROM trades 
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """, (cutoff_str,))
        trades = cursor.fetchall()
        conn.close()
        
        if not trades:
            return {
                "period": period,
                "total_pnl": 0.0,
                "trade_count": 0,
                "buy_count": 0,
                "sell_count": 0,
                "win_rate": 0.0,
                "total_volume": 0.0
            }
        
        total_pnl = sum(t[4] or 0 for t in trades)
        buy_count = sum(1 for t in trades if t[0] == "buy")
        sell_count = sum(1 for t in trades if t[0] == "sell")
        wins = sum(1 for t in trades if (t[4] or 0) > 0)
        total_volume = sum(t[3] for t in trades)
        
        return {
            "period": period,
            "total_pnl": round(total_pnl, 2),
            "trade_count": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "win_rate": round(wins / len(trades) * 100, 1) if trades else 0.0,
            "total_volume": round(total_volume, 2)
        }
    
    def get_context_for_ai(self) -> str:
        """
        Generate context string for Unk AI queries.
        
        Returns:
            Formatted context with recent trades and P&L.
        """
        recent = self.get_recent_trades(limit=5)
        pnl_24h = self.get_pnl_summary("24h")
        pnl_7d = self.get_pnl_summary("7d")
        
        # Format trades
        trade_lines = []
        for t in recent:
            ts = t["timestamp"][:16].replace("T", " ")
            side = t["side"].upper()
            sym = t["symbol"].replace("-USD", "")
            qty = t["quantity"]
            price = t["price"]
            pnl_str = f" P&L: ${t['pnl']:.2f}" if t.get("pnl") else ""
            trade_lines.append(f"  • {ts} {side} {qty:.4f} {sym} @ ${price:.2f}{pnl_str}")
        
        trades_text = "\n".join(trade_lines) if trade_lines else "  (No recent trades)"
        
        context = f"""
=== TRADING CONTEXT ===
24h P&L: ${pnl_24h['total_pnl']:.2f} ({pnl_24h['trade_count']} trades, {pnl_24h['win_rate']:.0f}% win rate)
7d P&L: ${pnl_7d['total_pnl']:.2f} ({pnl_7d['trade_count']} trades)

RECENT TRADES:
{trades_text}
=======================
"""
        return context.strip()


# Singleton instance
trading_memory = TradingMemory()


if __name__ == "__main__":
    # Self-test
    logging.basicConfig(level=logging.INFO)
    tm = TradingMemory()
    
    print("Testing TradingMemory...")
    
    # Log a test trade
    trade_id = tm.log_trade(
        symbol="BTC-USD",
        side="buy",
        quantity=0.001,
        price=43250.00,
        strategy="test",
        reason="Self-test trade"
    )
    print(f"Logged trade: {trade_id}")
    
    # Get recent trades
    recent = tm.get_recent_trades(limit=5)
    print(f"Recent trades: {len(recent)}")
    
    # Get P&L
    pnl = tm.get_pnl_summary("24h")
    print(f"24h P&L: {pnl}")
    
    # Get context
    ctx = tm.get_context_for_ai()
    print(f"\nAI Context:\n{ctx}")
