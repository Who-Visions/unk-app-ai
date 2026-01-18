"""
Massive (Polygon) WebSocket Client
==================================
Attempts to stream real-time or delayed crypto data.
"""
import websocket
import json
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MASSIVE_API_KEY")

class MassiveStream:
    def __init__(self, url="wss://socket.polygon.io/crypto"):
        self.url = url
        self.ws = None
        self.connected = False
        
    def on_message(self, ws, message):
        msgs = json.loads(message)
        for m in msgs:
            ev = m.get('ev')
            sym = m.get('pair') or m.get('sym')
            if ev == 'status':
                print(f"🔧 STATUS: {m.get('message')}")
            elif ev == 'XT': # Trade
                p = m.get('p')
                s = m.get('s')
                print(f"💰 TRADE: {sym} @ ${p} (Vol: {s})")
            elif ev == 'XA': # Aggregate
                c = m.get('c')
                print(f"📊 AGG: {sym} Close: ${c}")
            else:
                print(f"📩 MSG: {m}")

    def on_error(self, ws, error):
        print(f"❌ ERROR: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 DISCONNECTED")
        self.connected = False

    def on_open(self, ws):
        print("🔌 CONNECTED")
        self.connected = True
        
        # Auth
        print("🔑 Authenticating...")
        auth_msg = {"action": "auth", "params": API_KEY}
        ws.send(json.dumps(auth_msg))
        
        # Subscribe
        # Try both XT (Trades) and XA (Aggregates) for XTZ-USD
        # Format usually X.BTC-USD or X:BTC-USD
        print("📡 Subscribing to XTZ-USD...")
        sub_msg = {"action": "subscribe", "params": "XT.XTZ-USD,XA.XTZ-USD"}
        ws.send(json.dumps(sub_msg))

    def run(self):
        # Enable trace for debugging
        # websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(self.url,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.run_forever()

if __name__ == "__main__":
    # Attempt Delayed Massive Endpoint (Last Resort)
    print("🚀 Starting Massive Stream (Delayed Test)...")
    stream = MassiveStream(url="wss://delayed.massive.com/crypto")
    stream.run()
