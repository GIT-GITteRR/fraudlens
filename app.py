"""
FraudLens - Enterprise Graph Fraud Investigation Console (app.py)

Designed to Google Stitch "Mission-Critical Financial Forensics" specification.
Theme: Dark Navy Enterprise Fintech (#0B1326 / #131B2E) with Precision Blue Accents.
Uses FalkorDB query results as the single source of truth.
Includes interactive PyVis graph visualization with fallback tables.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from graph_db import (
    check_connection,
    get_graph_overview_counts,
    get_account_transactions,
    get_account_devices,
    get_account_neighborhood_subgraph
)
from seed_data import seed_database
from risk_engine import calculate_account_risk, get_all_account_risk_summaries, RiskConfig
from graph_viz import build_network_html
from ai_assistant import query_llm_assistant

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FraudLens | Financial Forensics Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Google Stitch Design System: Mission-Critical Financial Forensics CSS
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #DAE2FD;
    }

    .mono-data {
        font-family: 'JetBrains Mono', monospace;
    }

    /* Enterprise Masthead Banner */
    .stitch-masthead {
        background: linear-gradient(180deg, #131B2E 0%, #0B1326 100%);
        border: 1px solid #222A3D;
        border-radius: 6px;
        padding: 18px 24px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 16px rgba(6, 14, 32, 0.4);
    }
    .masthead-title h1 {
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        color: #F8FAFC !important;
        margin: 0 !important;
        letter-spacing: -0.025em;
    }
    .masthead-subtitle {
        color: #8C909F;
        font-size: 0.82rem;
        margin-top: 4px;
    }

    /* Synthetic Data Compliance Badge */
    .synthetic-badge {
        background-color: rgba(59, 130, 246, 0.12);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.35);
        padding: 5px 12px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* 4 Metric Cards (Google Stitch Layer 2) */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 22px;
    }
    .metric-tile {
        background: #131B2E;
        border: 1px solid #222A3D;
        border-radius: 6px;
        padding: 14px 18px;
        transition: border-color 0.15s ease;
    }
    .metric-tile:hover {
        border-color: #334155;
    }
    .metric-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8C909F;
        margin-bottom: 6px;
    }
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.65rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.2;
    }
    .metric-delta-alert {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #EF4444;
        font-weight: 600;
        margin-top: 4px;
    }
    .metric-delta-ok {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #10B981;
        font-weight: 500;
        margin-top: 4px;
    }

    /* Selected Account Risk Panel */
    .risk-hero-card {
        background: #171F33;
        border: 1px solid #2D3449;
        border-radius: 6px;
        padding: 20px;
        margin-bottom: 18px;
    }
    .risk-header-flex {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 14px;
    }
    .risk-account-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.3rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .risk-score-badge {
        padding: 6px 14px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 0.88rem;
    }
    .risk-high {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid #EF4444;
    }
    .risk-medium {
        background: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid #F59E0B;
    }
    .risk-low {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid #10B981;
    }

    /* Evidence Tag Chips */
    .evidence-chip {
        display: inline-block;
        background: #0B1326;
        color: #ADC6FF;
        border: 1px solid #334155;
        border-radius: 3px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        padding: 2px 7px;
        margin: 2px 4px 4px 0;
    }

    /* Signal Factor Row */
    .signal-item {
        background: #131B2E;
        border-left: 3px solid #3B82F6;
        border-top: 1px solid #222A3D;
        border-right: 1px solid #222A3D;
        border-bottom: 1px solid #222A3D;
        border-radius: 0 4px 4px 0;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .signal-item-high {
        border-left-color: #EF4444;
    }
    .signal-title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    .signal-name {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        color: #DAE2FD;
    }
    .signal-points {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        color: #60A5FA;
    }
    .signal-desc {
        font-size: 0.8rem;
        color: #94A3B8;
        line-height: 1.35;
    }

    /* Interactive Graph Visualizer Shell */
    .graph-container {
        background: #0B1326;
        border: 1px solid #222A3D;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 16px;
    }
    .graph-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        align-items: center;
        background: #131B2E;
        border: 1px solid #222A3D;
        border-radius: 4px;
        padding: 8px 14px;
        margin-bottom: 10px;
        font-size: 0.75rem;
        color: #DAE2FD;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .legend-indicator {
        width: 10px;
        height: 10px;
        display: inline-block;
    }

    /* Connected Hardware Cards */
    .hardware-card {
        background: #131B2E;
        border: 1px solid #222A3D;
        border-radius: 6px;
        padding: 14px;
        margin-bottom: 10px;
    }
    .hardware-card-shared {
        border-left: 3px solid #EF4444;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Top Professional Header with Stitch Enterprise Styling
# -----------------------------------------------------------------------------
st.markdown("""
<div class="stitch-masthead">
    <div class="masthead-title">
        <div>
            <h1>🛡️ FraudLens <span style="font-size: 0.9rem; font-weight: 400; color: #8C909F;">| Financial Forensics Console</span></h1>
            <div class="masthead-subtitle">Mission-Critical Graph Ring Triage &amp; Explainable Risk Prioritization • Powered by <strong>FalkorDB</strong></div>
        </div>
    </div>
    <div>
        <span class="synthetic-badge">🧪 Synthetic Demo Data</span>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sidebar Navigation & Investigation Parameters
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧭 Navigation & Mode")
    nav_mode = st.radio(
        "Workspace View",
        options=["Triage Queue & Dossier", "Ledger & Graph Entities", "Forensics Rules Guide"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### ⚡ Database Telemetry")
    conn_status = check_connection()
    if conn_status["status"] == "ok":
        st.success("🟢 FalkorDB Cloud Online")
    else:
        st.error("🔴 FalkorDB Disconnected")
        st.caption(f"Reason: {conn_status['message']}")
        st.info("Check your .env settings (FALKORDB_HOST, FALKORDB_PORT, FALKORDB_PASSWORD).")

    st.markdown("---")
    st.markdown("### ⚙️ Investigation Heuristics")
    high_threshold = st.number_input(
        "High-Value Threshold (₹)",
        min_value=500.0,
        max_value=100000.0,
        value=5000.0,
        step=500.0,
        help="Outbound single transfer threshold (+15 pts)."
    )
    burst_window = st.slider(
        "Velocity Window (Minutes)",
        min_value=15,
        max_value=360,
        value=120,
        step=15,
        help="Timeframe to detect rapid fund movement (+20 pts)."
    )

    active_config = RiskConfig(
        high_amount_threshold=float(high_threshold),
        burst_window_minutes=int(burst_window)
    )

    st.markdown("---")
    st.markdown("### 🛠️ Actions")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Refresh", use_container_width=True, help="Re-query FalkorDB"):
            st.rerun()
    with col_btn2:
        if st.button("🌱 Re-Seed", use_container_width=True, help="Reset to standard 20 accounts demo dataset"):
            with st.spinner("Seeding demo graph..."):
                res = seed_database(reset=True)
                st.success("Graph reset & seeded!")
                st.rerun()

    st.markdown("---")
    st.markdown("### 🤖 AI Copilot Config")
    api_key_input = st.text_input(
        "Gemini API Key (Optional)",
        type="password",
        help="If not provided, the assistant automatically uses the Deterministic FalkorDB Engine."
    )

    st.markdown("---")
    st.caption("🔒 **Investigative Disclaimer:** Scores are priority rankings to focus review queues, not proof of wrongdoing or probability of fraud.")

# -----------------------------------------------------------------------------
# Database Verification: Fetch Actual Graph Overview Counts
# -----------------------------------------------------------------------------
overview = get_graph_overview_counts()

if overview["total_accounts"] == 0:
    st.warning("⚠️ **FalkorDB Graph is currently unpopulated.**")
    st.info("No synthetic financial entities exist in the database yet. Click below to initialize the demo dataset.")
    if st.button("🌱 Initialize Synthetic Dataset (20 Accounts, 8 Devices, 40 Transactions)", type="primary"):
        with st.spinner("Seeding graph in FalkorDB..."):
            seed_database(reset=True)
            st.rerun()
    st.stop()

# -----------------------------------------------------------------------------
# Fetch Account Summaries from FalkorDB
# -----------------------------------------------------------------------------
try:
    account_summaries = get_all_account_risk_summaries(config=active_config)
except Exception as e:
    st.error(f"Failed to query FalkorDB: {e}")
    st.stop()

high_priority_count = sum(1 for a in account_summaries if a["risk_level"] == "High")
medium_priority_count = sum(1 for a in account_summaries if a["risk_level"] == "Medium")
low_priority_count = sum(1 for a in account_summaries if a["risk_level"] == "Low")

# -----------------------------------------------------------------------------
# Component: Four Overview Metric Cards
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="metric-grid">
    <div class="metric-tile">
        <div class="metric-label">Total Accounts</div>
        <div class="metric-value">{overview['total_accounts']}</div>
        <div class="metric-delta-ok">● Active in Graph</div>
    </div>
    <div class="metric-tile">
        <div class="metric-label">Tracked Devices</div>
        <div class="metric-value">{overview['total_devices']}</div>
        <div class="metric-delta-ok">● Hardware Fingerprints</div>
    </div>
    <div class="metric-tile">
        <div class="metric-label">Graph Transactions</div>
        <div class="metric-value">{overview['total_transactions']}</div>
        <div class="metric-delta-ok">● Verified Transfers</div>
    </div>
    <div class="metric-tile" style="border-left: 3px solid {'#EF4444' if high_priority_count > 0 else '#334155'};">
        <div class="metric-label">High Priority Queue</div>
        <div class="metric-value" style="color: {'#F87171' if high_priority_count > 0 else '#DAE2FD'};">{high_priority_count}</div>
        <div class="{'metric-delta-alert' if high_priority_count > 0 else 'metric-delta-ok'}">
            {'🚨 Needs Immediate Review' if high_priority_count > 0 else '● Zero High Alerts'}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# View Routing
# -----------------------------------------------------------------------------
if nav_mode == "Triage Queue & Dossier":
    col_queue, col_dossier = st.columns([1, 1], gap="medium")

    # -------------------------------------------------------------------------
    # Left Panel: Readable Suspicious Account Table
    # -------------------------------------------------------------------------
    with col_queue:
        st.subheader("📋 Priority Triage Queue")
        st.caption("Accounts ranked deterministically by graph risk signals:")

        table_rows = []
        for item in account_summaries:
            sig_names = [f["signal_name"] for f in item["factors"]]
            table_rows.append({
                "Account ID": item["account_id"],
                "Priority": item["risk_level"],
                "Score": item["risk_score"],
                "Signals": len(item["factors"]),
                "Key Signals": ", ".join(sig_names) if sig_names else "Clean Baseline"
            })

        df_accounts = pd.DataFrame(table_rows)

        def style_priority(val):
            if val == "High":
                return "background-color: rgba(239, 68, 68, 0.2); color: #F87171; font-weight: 600;"
            elif val == "Medium":
                return "background-color: rgba(245, 158, 11, 0.2); color: #FBBF24; font-weight: 600;"
            return "background-color: rgba(16, 185, 129, 0.12); color: #34D399;"

        styled_table = df_accounts.style.map(style_priority, subset=["Priority"])
        st.dataframe(styled_table, use_container_width=True, hide_index=True, height=440)
        st.caption("💡 Select an Account on the right panel to inspect connected forensic evidence and interactive graph.")

    # -------------------------------------------------------------------------
    # Right Panel: Prominent Selected Account Risk Panel & Evidence
    # -------------------------------------------------------------------------
    with col_dossier:
        st.subheader("🔬 Account Forensic Dossier")

        account_ids = [a["account_id"] for a in account_summaries]
        selected_id = st.selectbox(
            "Target Account to Investigate:",
            options=account_ids,
            index=0,
            format_func=lambda x: f"{x} - {next((a.get('account_name', x) for a in account_summaries if a['account_id'] == x), '')} [{next((a['risk_level'] for a in account_summaries if a['account_id'] == x), '')}]"
        )

        if selected_id:
            dossier = calculate_account_risk(selected_id, config=active_config)
            score = dossier["risk_score"]
            level = dossier["risk_level"]
            badge_class = "risk-high" if level == "High" else ("risk-medium" if level == "Medium" else "risk-low")

            # Prominent Risk Hero Card
            st.markdown(f"""
            <div class="risk-hero-card">
                <div class="risk-header-flex">
                    <div>
                        <div class="risk-account-id">{dossier['account_id']} <span style="font-size: 0.95rem; font-weight: 400; color: #8C909F;">({dossier.get('account_name', 'Account')})</span></div>
                        <div style="font-size: 0.8rem; color: #8C909F; margin-top: 3px;">FalkorDB Node: <code>:Account {{id: '{dossier['account_id']}'}}</code></div>
                    </div>
                    <div class="risk-score-badge {badge_class}">
                        {level.upper()} PRIORITY • {score}/100
                    </div>
                </div>
                <div style="font-size: 0.82rem; color: #DAE2FD; line-height: 1.4;">
                    {dossier['investigation_disclaimer']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Evidence Section with IDs and Explanations
            st.markdown("#### 📑 Linked Evidence Identifiers")
            if dossier["evidence_ids"]:
                chips_html = "".join([f'<span class="evidence-chip">{eid}</span>' for eid in dossier["evidence_ids"]])
                st.markdown(chips_html, unsafe_allow_html=True)
            else:
                st.caption("No suspicious entity identifiers connected.")

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.markdown("#### 🚨 Triggered Graph Signals")
            if dossier["factors"]:
                for factor in dossier["factors"]:
                    is_crimson = "HIGH" in factor["signal_name"] or "BURST" in factor["signal_name"] or "MULTI" in factor["signal_name"]
                    st.markdown(f"""
                    <div class="signal-item {'signal-item-high' if is_crimson else ''}">
                        <div class="signal-title-row">
                            <span class="signal-name">{factor['signal_name']}</span>
                            <span class="signal-points">+{factor['points']} PTS</span>
                        </div>
                        <div class="signal-desc">{factor['explanation']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ **Clean Baseline:** No shared devices, abnormal velocity, or multi-sender loops detected for this entity.")

            # Grounded Forensic AI Assistant
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            with st.expander("🤖 Forensic AI Copilot (Grounded Assistant)", expanded=True):
                st.caption(f"Ask questions about Account `{selected_id}`. Grounded strictly on FalkorDB records.")
                user_q = st.text_input(
                    "Investigator Query:",
                    placeholder="e.g. Why was this account prioritized? What devices are shared?",
                    key=f"q_{selected_id}"
                )
                btn_c1, btn_c2 = st.columns(2)
                with btn_c1:
                    analyze_btn = st.button("🔎 Analyze Evidence", key=f"ask_{selected_id}", use_container_width=True)
                with btn_c2:
                    summary_btn = st.button("📑 Forensic Summary", key=f"sum_{selected_id}", use_container_width=True)

                if analyze_btn or summary_btn:
                    prompt_q = user_q if (analyze_btn and user_q) else f"Summarize key forensic signals and supporting entity IDs for {selected_id}."
                    with st.spinner("Analyzing graph records..."):
                        ai_res = query_llm_assistant(
                            selected_id,
                            prompt_q,
                            config=active_config,
                            api_key_override=api_key_input if api_key_input else None
                        )
                        st.caption(f"Analysis Engine: `{ai_res['provider']}`")
                        st.markdown(ai_res["answer"])
                        if ai_res["evidence_ids"]:
                            st.caption(f"Citing Evidence IDs: {', '.join(ai_res['evidence_ids'])}")

    # -------------------------------------------------------------------------
    # Full-Width Lower Section: Interactive Network Graph & Evidence Ledgers
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader(f"🌐 Connected Entities & Forensic Graph for `{selected_id}`")
    st.caption("Interactive graph traversal, transaction ledger, and hardware ring associations:")

    tab_network, tab_tx, tab_dev = st.tabs([
        "🕸️ Interactive Network Graph (FalkorDB)",
        "💳 Transaction Ledger (Cypher Table)",
        "📱 Hardware & Shared Device Ring"
    ])

    # 1. Interactive Network Graph (PyVis)
    with tab_network:
        # Visual Legend
        st.markdown("""
        <div class="graph-legend">
            <span class="legend-item"><span class="legend-indicator" style="background: #F59E0B; border-radius: 50%;"></span> <strong>Selected Account (Focal Node)</strong></span>
            <span class="legend-item"><span class="legend-indicator" style="background: #3B82F6; border-radius: 50%;"></span> <span>Connected Account</span></span>
            <span class="legend-item"><span class="legend-indicator" style="background: #10B981; border-radius: 2px;"></span> <span>Hardware Device (<code>USES</code>)</span></span>
            <span class="legend-item"><span class="legend-indicator" style="background: #EF4444; transform: rotate(45deg);"></span> <span>Transaction (<code>MADE</code> / <code>TO_ACCOUNT</code>)</span></span>
        </div>
        """, unsafe_allow_html=True)

        try:
            subgraph = get_account_neighborhood_subgraph(selected_id)
            if subgraph["nodes"]:
                html_net = build_network_html(subgraph, height="450px")
                if html_net:
                    components.html(html_net, height=470, scrolling=False)
                    st.caption(f"⚡ Interactive Vis.js Canvas: Drag nodes to explore. Scroll to zoom. Sourced from FalkorDB ({len(subgraph['nodes'])} nodes, {len(subgraph['edges'])} edges).")
                else:
                    st.info(f"No connected entities found for Account `{selected_id}`.")
            else:
                st.info(f"ℹ️ Account `{selected_id}` has no connected graph relationships recorded.")
        except Exception as e:
            st.error(f"Network visualizer encountered an issue: {e}")
            st.info("Falling back to tabular transaction and hardware records below.")

    # 2. Transaction Ledger (Table Fallback)
    with tab_tx:
        st.caption(f"Actual verified inbound/outbound transfer edges connected to `{selected_id}` in FalkorDB:")
        txs = get_account_transactions(selected_id)
        if txs:
            df_tx = pd.DataFrame(txs).drop(columns=["Raw Amount"], errors="ignore")
            st.dataframe(df_tx, use_container_width=True, hide_index=True)
        else:
            st.info(f"No direct transactions recorded in FalkorDB for `{selected_id}`.")

    # 3. Hardware & Shared Device Ring Inspector
    with tab_dev:
        st.caption(f"Physical hardware associations: `(:Account {{id: '{selected_id}'}})-[:USED_DEVICE]->(:Device)`")
        devs = get_account_devices(selected_id)
        if devs:
            for d in devs:
                is_shared = d["Is Shared"]
                shared_card_class = "hardware-card hardware-card-shared" if is_shared else "hardware-card"
                st.markdown(f"""
                <div class="{shared_card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div>
                            <strong style="color: #F8FAFC;">Device ID: <code>{d['Device ID']}</code></strong>
                            <span style="color: #8C909F; font-size: 0.8rem; margin-left: 8px;">({d['Device Type']} • {d['Operating System']})</span>
                        </div>
                        <div>
                            {'<span style=\"color: #F87171; font-weight: 600; font-size: 0.75rem;\">⚠️ SHARED DEVICE RING DETECTED</span>' if is_shared else '<span style=\"color: #34D399; font-size: 0.75rem;\">🔒 Dedicated Hardware (No sharing)</span>'}
                        </div>
                    </div>
                    <div style="font-size: 0.82rem; color: #DAE2FD;">
                        {'<strong>Other Accounts Authenticating from this Device:</strong> ' + ', '.join([f'<code>{a}</code>' for a in d['Shared Co-Accounts']]) if is_shared else 'Single account attribution in graph.'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No device associations found in graph for `{selected_id}`.")

elif nav_mode == "Ledger & Graph Entities":
    st.subheader("🌐 Connected Entities & Forensic Graph Records")
    
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        target_id = st.selectbox(
            "Select Account to Inspect:",
            options=[a["account_id"] for a in account_summaries],
            key="ledger_select"
        )

    tab_network2, tab_tx2, tab_dev2 = st.tabs([
        "🕸️ Interactive Graph",
        "💳 Transaction Ledger",
        "📱 Hardware Devices"
    ])

    with tab_network2:
        subgraph2 = get_account_neighborhood_subgraph(target_id)
        if subgraph2["nodes"]:
            html_net2 = build_network_html(subgraph2, height="500px")
            if html_net2:
                components.html(html_net2, height=520, scrolling=False)
        else:
            st.info(f"No connected entities found for Account `{target_id}`.")

    with tab_tx2:
        txs = get_account_transactions(target_id)
        if txs:
            df_tx = pd.DataFrame(txs).drop(columns=["Raw Amount"], errors="ignore")
            st.dataframe(df_tx, use_container_width=True, hide_index=True)
        else:
            st.info(f"No direct transactions recorded in FalkorDB for `{target_id}`.")

    with tab_dev2:
        devs = get_account_devices(target_id)
        if devs:
            for d in devs:
                is_shared = d["Is Shared"]
                shared_card_class = "hardware-card hardware-card-shared" if is_shared else "hardware-card"
                st.markdown(f"""
                <div class="{shared_card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div>
                            <strong style="color: #F8FAFC;">Device: {d['Device ID']}</strong>
                            <span style="color: #8C909F; font-size: 0.8rem; margin-left: 8px;">({d['Device Type']} • {d['Operating System']})</span>
                        </div>
                        <div>
                            {'<span style=\"color: #F87171; font-weight: 600; font-size: 0.75rem;\">⚠️ SHARED DEVICE RING</span>' if is_shared else '<span style=\"color: #34D399; font-size: 0.75rem;\">🔒 Dedicated Hardware</span>'}
                        </div>
                    </div>
                    <div style="font-size: 0.82rem; color: #DAE2FD;">
                        {'<strong>Co-Accounts Sharing Hardware:</strong> ' + ', '.join([f'<code>{a}</code>' for a in d['Shared Co-Accounts']]) if is_shared else 'Single account attribution in graph.'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No device associations found in graph for `{target_id}`.")

elif nav_mode == "Forensics Rules Guide":
    st.subheader("📖 FraudLens Investigation Rules & Architecture")
    st.markdown("""
    ### Graph-Based Detection vs. Traditional Relational Rules
    Traditional SQL queries struggle with multi-hop relationships. FraudLens leverages **FalkorDB's OpenCypher engine** to evaluate graph topologies in sub-milliseconds:

    1. **`SHARED_DEVICE` (+25 Points):**
       ```cypher
       MATCH (a:Account {id: $account_id})-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(other:Account)
       WHERE other.id <> a.id
       RETURN d.id, collect(DISTINCT other.id)
       ```
    2. **`MULTI_SENDER_DESTINATION` (+20 Points):**
       Identifies funnel and muling destinations that receive funds from multiple sender accounts in coordinated transfer rings.
    3. **`HIGH_VALUE_TRANSACTION` (+15 Points):**
       Flags single transfers exceeding the configurable threshold (default: ₹5,000.00).
    4. **`HIGH_VELOCITY_BURST` (+20 Points):**
       Detects multiple outbound transfers clustered within a short temporal window (default: 120 minutes).
    """)
