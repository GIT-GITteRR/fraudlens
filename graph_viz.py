"""
FraudLens - Interactive Graph Network Visualizer (graph_viz.py)

Generates lightweight, self-contained, interactive physics-based network visualizations
using Vis.js standalone, styled to match the dark-navy enterprise fintech theme.
Eliminates fragile relative bindings and works seamlessly inside Streamlit iframes.
"""

import json
import html
from typing import Dict, Any, Optional


def build_network_html(subgraph: Dict[str, Any], height: str = "480px") -> Optional[str]:
    """
    Builds a robust, standalone Vis.js HTML graph from a FalkorDB neighborhood subgraph.
    Renders directly in a sandboxed Streamlit iframe without broken relative dependencies.
    """
    nodes = subgraph.get("nodes", [])
    edges = subgraph.get("edges", [])

    if not nodes:
        return None

    vis_nodes = []
    for node in nodes:
        node_id = str(node["id"])
        node_type = node.get("type", "Unknown")
        is_target = node.get("is_target", False)
        raw_label = str(node.get("label", node_id))
        safe_label = html.escape(raw_label)
        detail = html.escape(str(node.get("detail", "")))

        if is_target:
            vis_nodes.append({
                "id": node_id,
                "label": safe_label,
                "title": f"Target Account: {safe_label}\n{detail}",
                "color": {
                    "background": "#F59E0B",
                    "border": "#D97706",
                    "highlight": {"background": "#FBBF24", "border": "#FFFFFF"}
                },
                "shape": "dot",
                "size": 30,
                "borderWidth": 3,
                "font": {"size": 13, "face": "Inter, sans-serif", "color": "#F8FAFC", "bold": True}
            })
        elif node_type == "Account":
            vis_nodes.append({
                "id": node_id,
                "label": safe_label,
                "title": f"Account: {safe_label}\n{detail}",
                "color": {
                    "background": "#3B82F6",
                    "border": "#1D4ED8",
                    "highlight": {"background": "#60A5FA", "border": "#FFFFFF"}
                },
                "shape": "dot",
                "size": 20,
                "borderWidth": 2,
                "font": {"size": 11, "face": "Inter, sans-serif", "color": "#DAE2FD"}
            })
        elif node_type == "Device":
            vis_nodes.append({
                "id": node_id,
                "label": safe_label,
                "title": f"Hardware Device: {safe_label}\n{detail}",
                "color": {
                    "background": "#10B981",
                    "border": "#047857",
                    "highlight": {"background": "#34D399", "border": "#FFFFFF"}
                },
                "shape": "hexagon",
                "size": 22,
                "borderWidth": 2,
                "font": {"size": 11, "face": "Inter, sans-serif", "color": "#DAE2FD"}
            })
        elif node_type == "Transaction":
            vis_nodes.append({
                "id": node_id,
                "label": safe_label,
                "title": f"Transaction: {safe_label}\n{detail}",
                "color": {
                    "background": "#EF4444",
                    "border": "#B91C1C",
                    "highlight": {"background": "#F87171", "border": "#FFFFFF"}
                },
                "shape": "diamond",
                "size": 16,
                "borderWidth": 2,
                "font": {"size": 10, "face": "JetBrains Mono, monospace", "color": "#FCA5A5"}
            })
        else:
            vis_nodes.append({
                "id": node_id,
                "label": safe_label,
                "title": safe_label,
                "color": {"background": "#64748B", "border": "#475569"},
                "shape": "dot",
                "size": 14,
                "borderWidth": 1,
                "font": {"size": 10, "color": "#DAE2FD"}
            })

    vis_edges = []
    for edge in edges:
        from_id = str(edge["from"])
        to_id = str(edge["to"])
        raw_label = str(edge.get("label", ""))
        safe_label = html.escape(raw_label)

        if safe_label == "USES":
            edge_color = "#10B981"
        elif safe_label in ["MADE", "INITIATED"]:
            edge_color = "#60A5FA"
        elif safe_label in ["TO_ACCOUNT", "BENEFICIARY"]:
            edge_color = "#38BDF8"
        else:
            edge_color = "#475569"

        vis_edges.append({
            "from": from_id,
            "to": to_id,
            "label": safe_label,
            "arrows": "to",
            "color": {"color": edge_color, "highlight": "#F8FAFC"},
            "title": f"Relationship: {safe_label}",
            "font": {
                "size": 9,
                "face": "JetBrains Mono, monospace",
                "color": "#8C909F",
                "strokeWidth": 0,
                "align": "middle"
            },
            "smooth": {"type": "cubicBezier", "roundness": 0.2}
        })

    nodes_json = json.dumps(vis_nodes)
    edges_json = json.dumps(vis_edges)
    height_css = height if height.endswith("px") else f"{height}px"

    html_template = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    html, body {{
      width: 100%;
      height: 100%;
      background-color: #0B1326;
      overflow: hidden;
      font-family: 'Inter', -apple-system, sans-serif;
    }}
    #mynetwork {{
      width: 100%;
      height: {height_css};
      background: #0B1326;
      border: 1px solid #222A3D;
      border-radius: 6px;
    }}
    .vis-tooltip {{
      position: absolute;
      background-color: #1E293B !important;
      color: #F8FAFC !important;
      border: 1px solid #475569 !important;
      border-radius: 4px !important;
      padding: 8px 12px !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 12px !important;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
      z-index: 999999 !important;
      pointer-events: none;
    }}
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>
</head>
<body>
  <div id="mynetwork"></div>
  <script>
    (function() {{
      var container = document.getElementById('mynetwork');
      var nodes = new vis.DataSet({nodes_json});
      var edges = new vis.DataSet({edges_json});
      var data = {{ nodes: nodes, edges: edges }};
      var options = {{
        nodes: {{
          borderWidth: 2,
          borderWidthSelected: 3
        }},
        edges: {{
          arrows: {{
            to: {{ enabled: true, scaleFactor: 0.7 }}
          }},
          hoverWidth: 1.5
        }},
        physics: {{
          barnesHut: {{
            gravitationalConstant: -2800,
            centralGravity: 0.3,
            springLength: 120,
            springConstant: 0.04,
            damping: 0.95,
            avoidOverlap: 0.4
          }},
          minVelocity: 0.75,
          solver: 'barnesHut',
          stabilization: {{
            enabled: true,
            iterations: 150,
            updateInterval: 25
          }}
        }},
        interaction: {{
          hover: true,
          tooltipDelay: 100,
          zoomView: true,
          dragView: true,
          navigationButtons: false,
          keyboard: false
        }}
      }};

      var network = new vis.Network(container, data, options);

      network.once('stabilizationIterationsDone', function() {{
        network.fit({{ animation: {{ duration: 600, easingFunction: 'easeInOutQuad' }} }});
      }});

      window.addEventListener('resize', function() {{
        network.redraw();
        network.fit();
      }});
      
      // Secondary fit in case iframe was initially hidden by tabs
      setTimeout(function() {{
        network.redraw();
        network.fit();
      }}, 300);
      setTimeout(function() {{
        network.redraw();
        network.fit();
      }}, 800);
    }})();
  </script>
</body>
</html>
"""
    return html_template
