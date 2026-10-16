import os
import sys
from dotenv import load_dotenv
from falkordb import FalkorDB

# Load credentials from .env
load_dotenv()

host = os.getenv("FALKORDB_HOST", "").strip()
port_str = os.getenv("FALKORDB_PORT", "6379").strip()
password = os.getenv("FALKORDB_PASSWORD", "").strip()
username = os.getenv("FALKORDB_USERNAME", "").strip() or None

# Clean up host if user copied with protocol or port attached
if host.startswith("redis://"):
    host = host.replace("redis://", "")
elif host.startswith("rediss://"):
    host = host.replace("rediss://", "")

if ":" in host:
    # If host contains host:port, split them automatically
    parts = host.split(":")
    host = parts[0]
    port_str = parts[1]

if not host or "your-host-here" in host:
    print("[ERROR] FALKORDB_HOST is empty.")
    print("Please open your .env file and paste your host into: FALKORDB_HOST=...")
    sys.exit(1)

try:
    port = int(port_str)
except ValueError:
    print(f"[ERROR] Invalid port '{port_str}'. Port must be a number.")
    sys.exit(1)

print(f"Connecting to FalkorDB Cloud at {host}:{port}...")

connected = False
last_error = None

# Attempt 1: Standard connection
# Attempt 2: SSL connection (some cloud instances enforce SSL)
for use_ssl in [False, True]:
    try:
        db = FalkorDB(
            host=host,
            port=port,
            password=password if password else None,
            username=username,
            ssl=use_ssl
        )
        graph = db.select_graph("fraudlens_test")
        result = graph.query("RETURN 'Connection to FalkorDB successful!' AS status")

        print("\n" + "=" * 50)
        print("  SUCCESS! Connected to FalkorDB Cloud!")
        print(f"   Mode: {'SSL/TLS' if use_ssl else 'Standard'}")
        print(f"   Database Response: {result.result_set[0][0]}")
        print("=" * 50)
        connected = True
        break
    except Exception as e:
        last_error = e

if not connected:
    print("\n[FAILED] Could not connect to FalkorDB.")
    print(f"Details: {last_error}")
    print("\nPlease verify:")
    print("1. Your database is finished deploying and has an 'Active' / 'Running' status.")
    print("2. Your FALKORDB_HOST in .env matches the Endpoint in your FalkorDB dashboard.")
    print("3. Your FALKORDB_PASSWORD in .env is correct.")
    sys.exit(1)
