# 🔍 FraudLens

> **FalkorDB Graph Hacks** Project  
> Real-Time Financial Fraud & Money Muling Ring Detection using Graph Databases.

---

## 💡 Overview

Traditional relational databases struggle to detect coordinated financial fraud because fraudsters operate in complex networks:
- **Circular Money Transfers:** Layered transactions where money moves `A -> B -> C -> A` to obscure origin.
- **Device & Identity Sharing:** Multiple distinct accounts logging in from the same rooted mobile device or anonymized proxy IP.

**FraudLens** leverages **FalkorDB's ultra-fast OpenCypher engine** to traverse interconnected entities in real time, score fraud risk with explainable factors, and visualize suspicious rings.

---

## 🏗️ Project Architecture

```text
FraudLens/
├── app.py              # Interactive Streamlit dashboard UI
├── graph_db.py         # FalkorDB client manager and query executor
├── seed_data.py        # Reproducible synthetic fraud data generator
├── risk_engine.py      # Graph topology explainable risk scoring
├── queries.cypher      # Core OpenCypher fraud detection queries
├── requirements.txt    # Project dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules (protects credentials & .venv)
└── README.md           # Documentation
```

---

## 🚀 Tech Stack

* **Language:** Python 3.14+
* **Graph Database:** [FalkorDB](https://www.falkordb.com/) (OpenCypher Query Engine)
* **Python SDK:** `falkordb-py` (v1.8.0)
* **Frontend:** Streamlit
* **Data Processing:** Pandas
* **Environment:** `python-dotenv`

---

## 🛠️ Getting Started

### 1. Prerequisites
* Python 3.10+ installed.
* Active FalkorDB instance (FalkorDB Cloud or local Docker).

### 2. Configure Environment
Copy the example environment file and add your credentials:
```bash
cp .env.example .env
```
Open `.env` and configure:
```env
FALKORDB_HOST=your-host.falkordb.cloud
FALKORDB_PORT=6379
FALKORDB_PASSWORD=your-password
FALKORDB_USERNAME=
FALKORDB_GRAPH_NAME=fraudlens
```

### 3. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Verify Database Connection
```bash
python test_connection.py
```

### 5. Seed Synthetic Fraud Data
```bash
python seed_data.py
```

### 6. Launch the Dashboard
```bash
streamlit run app.py
```

---

## 🔍 Core Fraud Patterns Detected

1. **Circular Money Muling:**
   ```cypher
   MATCH path = (a:Account)-[:TRANSFERRED_TO*2..4]->(a)
   RETURN path
   ```
2. **Device Sharing / Synthetic Farm:**
   ```cypher
   MATCH (u1:User)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(u2:User)
   WHERE u1.id <> u2.id
   RETURN d, collect(u1) + collect(u2)
   ```
3. **VPN & Proxy IP Clustering:**
   ```cypher
   MATCH (u:User)-[:LOGGED_IN_FROM]->(ip:IPAddress {is_vpn: true})
   RETURN ip, collect(u)
   ```

---

## 🛡️ Privacy & Safety
* Contains **zero real personal or financial information**.
* All generated entities are synthetic and reproducible.
* Secrets and credentials are strictly ignored via `.gitignore`.
