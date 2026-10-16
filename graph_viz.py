"""
FraudLens - Interactive Graph Network Visualizer (graph_viz.py)

Generates lightweight, interactive physics-based network visualizations
using PyVis and Vis.js, styled to match the dark-navy fintech theme.
"""

import html
from typing import Dict, Any, List, Optional
from pyvis.network import Network

def build_network_html(subgraph: Dict[str, Any], height: str = "480px") -> Optional[str]:
    """
    Builds an interactive vis.js HTML graph from a FalkorDB neighborhood subgraph.
    Returns None if the subgraph has no nodes.
    """
    nodes = subgraph.get("nodes", [])
    edges = subgraph.get("edges", [])

    if not nodes:
        return None

    # Initialize PyVis Network
    net = Network(
        height=height,
        width="100%",
        bgcolor="#0B1326",
        font_color="#DAE2FD",
        directed=True
    )

    # Configure physics for smooth, stable force-directed layout
    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 3,
        "font": {
          "size": 12,
          "face": "Inter, sans-serif",
          "color": "#DAE2FD"
        }
      },
      "edges": {
        "color": {
          "color": "#334155",
          "highlight": "#60A5FA",
          "hover": "#94A3B8"
        },
        "smooth": {
          "type": "cubicBezier",
          "roundness": 0.2
        },
        "font": {
          "size": 9,
          "face": "JetBrains Mono, monospace",
          "color": "#8C909F",
          "strokeWidth": 0,
          "align": "middle"
        },
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.6
          }
        }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -3200,
          "centralGravity": 0.25,
          "springLength": 130,
          "springConstant": 0.04,
          "damping": 0.95,
          "avoidOverlap": 0.3
        },
        "minVelocity": 0.75,
        "solver": "barnesHut"
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 150,
        "zoomView": true,
        "dragView": true
      }
    }
    """)

    # 1. Add Nodes with Distinct Visual Archetypes
    for node in nodes:
        node_id = str(node["id"])
        node_type = node.get("type", "Unknown")
        is_target = node.get("is_target", False)
        raw_label = str(node.get("label", node_id))
        safe_label = html.escape(raw_label)
        detail = html.escape(str(node.get("detail", "")))

        # Node styling based on entity archetype
        if is_target:
            # Selected Target Account (Prominent Amber Gold)
            color = {
                "background": "#F59E0B",
                "border": "#D97706",
                "highlight": {"background": "#FBBF24", "border": "#FFFFFF"}
            }
            shape = "dot"
            size = 28
            title = f"<b>🎯 Target Account: {safe_label}</b><br>{detail}"
            font = {"size": 13, "face": "JetBrains Mono, monospace", "color": "#F8FAFC", "vadjust": 0}
        elif node_type == "Account":
            # Connected Account (Electric Blue)
            color = {
                "background": "#3B82F6",
                "border": "#1D4ED8",
                "highlight": {"background": "#60A5FA", "border": "#FFFFFF"}
            }
            shape = "dot"
            size = 18
            title = f"<b>Account: {safe_label}</b><br>{detail}"
            font = {"size": 11, "face": "JetBrains Mono, monospace", "color": "#DAE2FD"}
        elif node_type == "Device":
            # Hardware Device (Emerald Green Hexagon)
            color = {
                "background": "#10B981",
                "border": "#047857",
                "highlight": {"background": "#34D399", "border": "#FFFFFF"}
            }
            shape = "hexagon"
            size = 22
            title = f"<b>📱 Hardware Device: {safe_label}</b><br>{detail}"
            font = {"size": 11, "face": "Inter, sans-serif", "color": "#DAE2FD"}
        elif node_type == "Transaction":
            # Transaction (Crimson Red Diamond)
            color = {
                "background": "#EF4444",
                "border": "#B91C1C",
                "highlight": {"background": "#F87171", "border": "#FFFFFF"}
            }
            shape = "diamond"
            size = 16
            title = f"<b>💳 Transaction: {safe_label}</b><br>{detail}"
            font = {"size": 10, "face": "JetBrains Mono, monospace", "color": "#FCA5A5"}
        else:
            color = {"background": "#64748B", "border": "#475569"}
            shape = "dot"
            size = 14
            title = safe_label
            font = {"size": 10, "color": "#DAE2FD"}

        net.add_node(
            n_id=node_id,
            label=safe_label,
            title=title,
            color=color,
            shape=shape,
            size=size,
            font=font
        )

    # 2. Add Labeled Edges (USES, MADE, TO_ACCOUNT)
    for edge in edges:
        from_id = str(edge["from"])
        to_id = str(edge["to"])
        raw_label = str(edge.get("label", ""))
        safe_edge_label = html.escape(raw_label)

        # Highlight edge color by relationship type
        if safe_edge_label == "USES":
            edge_color = "#10B981"  # Emerald for device link
        elif safe_edge_label in ["MADE", "TO_ACCOUNT"]:
            edge_color = "#60A5FA"  # Soft Blue for payment flow
        else:
            edge_color = "#334155"

        net.add_edge(
            source=from_id,
            to=to_id,
            label=safe_edge_label,
            color={"color": edge_color, "highlight": "#F8FAFC"},
            title=f"Relationship: {safe_edge_label}"
        )

    # Generate full self-contained HTML
    return net.generate_html()
