#!/usr/bin/env python3
"""
Generator Visualisasi Interaktif HTML untuk Graf Pengetahuan Hukum (GraphML)
Mengubah file GraphML (seperti gabungan.graphml) menjadi visualisasi HTML interaktif
berbasis Vis-Network yang ringan, modern, dan siap dibuka langsung di browser (Chrome/Edge/Firefox).
Dilengkapi dengan tabel metrik kustom di pojok sesuai permintaan pengguna.
"""

import os
import sys
import json
import argparse
import xml.etree.ElementTree as ET
from collections import Counter

# Palet Warna Elegan Berdasarkan Kategori Entitas Hukum
COLOR_PALETTE = {
    # Lapisan 1 (Silsilah Hukum Formal)
    "peraturan": {"bg": "#E11D48", "border": "#9F1239", "shape": "diamond", "size": 32},
    "putusanpengadilan": {"bg": "#7C3AED", "border": "#5B21B6", "shape": "star", "size": 28},
    "butiramar": {"bg": "#A855F7", "border": "#7E22CE", "shape": "dot", "size": 18},
    "pasal": {"bg": "#2563EB", "border": "#1D4ED8", "shape": "box", "size": 20},
    "versipasal": {"bg": "#0284C7", "border": "#0369A1", "shape": "ellipse", "size": 18},
    "peristiwaperubahan": {"bg": "#D97706", "border": "#B45309", "shape": "triangle", "size": 22},
    
    # Lapisan 2 (Substansi MiniRAG)
    "konsep": {"bg": "#059669", "border": "#047857", "shape": "dot", "size": 16},
    "pihak": {"bg": "#0D9488", "border": "#0F766E", "shape": "dot", "size": 18},
    "kewajiban": {"bg": "#4F46E5", "border": "#3730A3", "shape": "dot", "size": 16},
    "hak": {"bg": "#DB2777", "border": "#9D174D", "shape": "dot", "size": 16},
    "sanksi": {"bg": "#DC2626", "border": "#991B1B", "shape": "triangleDown", "size": 20},
    "tindak_pidana": {"bg": "#B91C1C", "border": "#7F1D1D", "shape": "square", "size": 20},
    "dasar_hukum": {"bg": "#EA580C", "border": "#C2410C", "shape": "box", "size": 18},
    
    # Default fallback
    "unknown": {"bg": "#64748B", "border": "#475569", "shape": "dot", "size": 15}
}


def parse_graphml(graphml_path: str):
    tree = ET.parse(graphml_path)
    root = tree.getroot()
    ns = {"g": "http://graphml.graphdrawing.org/xmlns"} if "}" in root.tag else {}
    
    key_map = {}
    for k in root.findall(".//g:key" if ns else ".//key", ns):
        key_map[k.attrib["id"]] = k.attrib.get("attr.name", k.attrib["id"])
        
    nodes = []
    edges = []
    
    node_elements = root.findall(".//g:node" if ns else ".//node", ns)
    for n in node_elements:
        nid = n.attrib["id"].strip('"')
        data = {}
        for d in n.findall("g:data" if ns else "data", ns):
            k_id = d.attrib.get("key", "")
            k_name = key_map.get(k_id, k_id)
            data[k_name] = d.text if d.text else ""
            
        etype = data.get("entity_type", "konsep").lower().strip()
        lapisan = str(data.get("lapisan", "2")).strip()
        desc = data.get("description", "").strip()
        eli_id = data.get("eli_id", "").strip()
        versi_id = data.get("versi_id", "").strip()
        
        style = COLOR_PALETTE.get(etype, COLOR_PALETTE["unknown"])
        size = style["size"]
        if etype == "peraturan":
            size = 35
        elif etype == "pasal":
            size = 22
            
        label = nid
        if len(label) > 28:
            short_label = label[:26] + "..."
        else:
            short_label = label

        nodes.append({
            "id": nid,
            "label": short_label,
            "title": f"<b>{nid}</b><br><i>Tipe: {etype} | Lapisan: {lapisan}</i>",
            "group": etype,
            "lapisan": lapisan,
            "full_name": nid,
            "description": desc,
            "eli_id": eli_id,
            "versi_id": versi_id,
            "color": {
                "background": style["bg"],
                "border": style["border"],
                "highlight": {"background": "#FBBF24", "border": "#D97706"}
            },
            "shape": style["shape"],
            "size": size,
            "font": {
                "color": "#FFFFFF" if style["shape"] == "box" else "#1E293B",
                "size": 13 if style["shape"] == "box" else 11,
                "face": "system-ui, -apple-system, sans-serif",
                "strokeWidth": 2 if style["shape"] != "box" else 0,
                "strokeColor": "#FFFFFF"
            }
        })
        
    edge_elements = root.findall(".//g:edge" if ns else ".//edge", ns)
    for idx, e in enumerate(edge_elements):
        s = e.attrib["source"].strip('"')
        t = e.attrib["target"].strip('"')
        data = {}
        for d in e.findall("g:data" if ns else "data", ns):
            k_id = d.attrib.get("key", "")
            k_name = key_map.get(k_id, k_id)
            data[k_name] = d.text if d.text else ""
            
        rel = data.get("relasi", "").strip()
        desc = data.get("description", "").strip()
        lap = str(data.get("lapisan", "2")).strip()
        
        edge_color = "#94A3B8"
        dashes = False
        if lap == "1":
            edge_color = "#3B82F6"
            dashes = False
        elif rel in ("menyesuaikan_pidana", "mengancamkan"):
            edge_color = "#EF4444"
            dashes = True
            
        edges.append({
            "id": f"e_{idx}",
            "from": s,
            "to": t,
            "label": rel if len(rel) <= 20 else rel[:18] + "..",
            "title": f"<b>Relasi:</b> {rel}<br>{desc}",
            "relasi": rel,
            "lapisan": lap,
            "color": {
                "color": edge_color,
                "highlight": "#F59E0B",
                "hover": "#2563EB"
            },
            "arrows": "to",
            "dashes": dashes,
            "font": {"size": 9, "align": "middle", "strokeWidth": 2, "strokeColor": "#FFFFFF"}
        })
        
    return nodes, edges


def generate_html(nodes, edges, output_path: str, title: str):
    nodes_json = json.dumps(nodes, ensure_ascii=False)
    edges_json = json.dumps(edges, ensure_ascii=False)
    
    etype_counts = Counter(n["group"] for n in nodes)
    lapisan_counts = Counter(n["lapisan"] for n in nodes)
    
    pills_html = ""
    for et, count in sorted(etype_counts.items(), key=lambda x: -x[1]):
        col = COLOR_PALETTE.get(et, COLOR_PALETTE["unknown"])["bg"]
        pills_html += f"""
        <button class="pill active" data-group="{et}" onclick="toggleGroup('{et}', this)" style="border-left: 4px solid {col};">
            <span class="pill-dot" style="background:{col};"></span>
            {et} <span class="badge">{count}</span>
        </button>
        """

    html_template = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #0B132B;
            color: #F8FAFC;
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        
        /* Top Navigation Header */
        header {{
            background: #141E33;
            border-bottom: 1px solid #1E293B;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 10;
        }}
        .header-title h1 {{
            font-size: 16px;
            font-weight: 700;
            color: #F8FAFC;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .header-title .tag {{
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 12px;
            background: #0284C7;
            color: #FFFFFF;
        }}
        .header-stats {{
            font-size: 13px;
            color: #94A3B8;
            display: flex;
            gap: 16px;
        }}
        .header-stats strong {{
            color: #38BDF8;
        }}
        
        /* Main Container */
        .main-container {{
            flex: 1;
            display: flex;
            position: relative;
            height: calc(100vh - 55px);
        }}
        
        #network {{
            flex: 1;
            height: 100%;
            background: radial-gradient(circle at center, #141E33 0%, #0B132B 100%);
        }}
        
        /* Floating Control Bar (Left) */
        .controls-bar {{
            position: absolute;
            top: 16px;
            left: 16px;
            background: rgba(20, 30, 51, 0.94);
            backdrop-filter: blur(8px);
            border: 1px solid #1E293B;
            padding: 12px;
            border-radius: 10px;
            z-index: 5;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 360px;
        }}
        .search-box input {{
            width: 100%;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #334155;
            background: #0B132B;
            color: #F8FAFC;
            font-size: 13px;
        }}
        .search-box input:focus {{
            outline: none;
            border-color: #38BDF8;
        }}
        .layer-tabs {{
            display: flex;
            gap: 6px;
        }}
        .layer-tab {{
            flex: 1;
            padding: 6px 8px;
            border-radius: 6px;
            border: 1px solid #334155;
            background: #141E33;
            color: #CBD5E1;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
            transition: all 0.2s;
        }}
        .layer-tab.active {{
            background: #0284C7;
            color: #FFFFFF;
            border-color: #38BDF8;
        }}
        .pills-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            max-height: 120px;
            overflow-y: auto;
            padding-right: 4px;
        }}
        .pill {{
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid #334155;
            background: #0B132B;
            color: #E2E8F0;
            font-size: 10px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: all 0.15s;
        }}
        .pill .badge {{
            background: #1E293B;
            padding: 1px 4px;
            border-radius: 4px;
            font-size: 9px;
            color: #94A3B8;
        }}
        .pill.active {{
            background: #141E33;
            color: #FFFFFF;
            border-color: #64748B;
        }}
        .pill.inactive {{
            opacity: 0.35;
        }}
        .btn-group {{
            display: flex;
            gap: 6px;
        }}
        .btn {{
            flex: 1;
            padding: 6px;
            border-radius: 6px;
            border: 1px solid #334155;
            background: #1E293B;
            color: #F8FAFC;
            font-size: 11px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.15s;
        }}
        .btn:hover {{
            background: #334155;
        }}

        /* Floating Summary Metrics Table (Corner Widget) */
        .metrics-overlay {{
            position: absolute;
            top: 16px;
            right: 16px;
            background: #0B132B;
            border: 1px solid #1E293B;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
            z-index: 6;
            overflow: hidden;
            min-width: 285px;
            transition: all 0.25s ease;
        }}
        .metrics-overlay.bottom-right {{
            top: auto;
            bottom: 20px;
            right: 20px;
        }}
        .metrics-overlay.bottom-left {{
            top: auto;
            bottom: 20px;
            left: 395px;
        }}
        .metrics-card-header {{
            background: #141E33;
            padding: 7px 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #1E293B;
            color: #94A3B8;
            font-size: 11px;
            font-weight: 600;
        }}
        .small-btn {{
            background: #0B132B;
            border: 1px solid #334155;
            color: #94A3B8;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            padding: 2px 7px;
            margin-left: 4px;
        }}
        .small-btn:hover {{
            color: #F8FAFC;
            background: #1E293B;
        }}
        .custom-metrics-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .custom-metrics-table th {{
            background: #0D1627;
            color: #38BDF8;
            padding: 9px 12px;
            text-align: left;
            font-size: 12px;
            font-weight: 700;
            border: 1px solid #1E293B;
        }}
        .custom-metrics-table th:last-child {{
            text-align: right;
            color: #FFFFFF;
        }}
        .custom-metrics-table td {{
            padding: 8px 12px;
            border: 1px solid #1E293B;
        }}
        .custom-metrics-table td.param-name {{
            color: #38BDF8;
            font-weight: 600;
            font-size: 11.5px;
        }}
        .custom-metrics-table td.param-val {{
            color: #FFFFFF;
            text-align: right;
            font-weight: 600;
            font-size: 11.5px;
        }}

        /* Floating Details Panel (Shown when Node is Clicked) */
        .info-panel {{
            position: absolute;
            top: 250px;
            right: 16px;
            width: 310px;
            max-height: calc(100vh - 320px);
            background: rgba(20, 30, 51, 0.95);
            backdrop-filter: blur(8px);
            border: 1px solid #1E293B;
            border-radius: 8px;
            padding: 14px;
            z-index: 5;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            overflow-y: auto;
            display: none;
        }}
        .info-panel.visible {{
            display: block;
        }}
        .info-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
            border-bottom: 1px solid #1E293B;
            padding-bottom: 6px;
        }}
        .info-header h2 {{
            font-size: 14px;
            color: #38BDF8;
            font-weight: 700;
            word-break: break-word;
        }}
        .close-btn {{
            background: none;
            border: none;
            color: #94A3B8;
            font-size: 18px;
            cursor: pointer;
        }}
        .info-section {{
            margin-bottom: 10px;
        }}
        .info-section label {{
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            color: #94A3B8;
            display: block;
            margin-bottom: 3px;
        }}
        .info-section .value {{
            font-size: 12px;
            color: #E2E8F0;
            line-height: 1.4;
            word-break: break-word;
        }}
        .tag-pill {{
            display: inline-block;
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 10.5px;
            font-weight: 600;
        }}
        .rel-item {{
            font-size: 11px;
            padding: 4px 6px;
            background: #0B132B;
            border-radius: 4px;
            margin-bottom: 4px;
            border-left: 3px solid #38BDF8;
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-title">
            <h1>🌐 {title}</h1>
            <span class="tag">Knowledge Graph V3</span>
        </div>
        <div class="header-stats">
            <div>Total Node: <strong>{len(nodes)}</strong></div>
            <div>Total Edge: <strong>{len(edges)}</strong></div>
            <div>Lapisan 1: <strong>{lapisan_counts.get('1', 0)}</strong></div>
            <div>Lapisan 2: <strong>{lapisan_counts.get('2', 0)}</strong></div>
        </div>
    </header>

    <div class="main-container">
        <!-- Floating Filter Sidebar (Left) -->
        <div class="controls-bar">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="🔍 Cari nama pasal / entitas..." onkeyup="searchNode(event)">
            </div>

            <div class="layer-tabs">
                <div class="layer-tab active" onclick="filterLapisan('all', this)">Semua Lapisan</div>
                <div class="layer-tab" onclick="filterLapisan('1', this)">Lapisan 1 (Silsilah)</div>
                <div class="layer-tab" onclick="filterLapisan('2', this)">Lapisan 2 (MiniRAG)</div>
            </div>

            <div style="font-size: 11px; color: #94A3B8; font-weight: 600;">Filter Tipe Entitas:</div>
            <div class="pills-container">
                {pills_html}
            </div>

            <div class="btn-group">
                <button class="btn" onclick="network.fit({{animation: true}})">🔄 Reset Zoom</button>
                <button class="btn" id="physicsBtn" onclick="togglePhysics()">⏸ Bekukan Posisi</button>
            </div>
        </div>

        <!-- Floating Summary Table (Top/Bottom Corner) Sesuai Permintaan -->
        <div class="metrics-overlay" id="metricsOverlay">
            <div class="metrics-card-header">
                <span>📊 Ringkasan Metrik Graf</span>
                <div>
                    <button class="small-btn" onclick="toggleCornerPos()" title="Pindah Posisi Pojok">⇄ Pindah Pojok</button>
                    <button class="small-btn" onclick="toggleTableVisibility()" id="toggleTblBtn" title="Sembunyikan/Tampilkan">−</button>
                </div>
            </div>
            <div id="tableContent">
                <table class="custom-metrics-table">
                    <thead>
                        <tr>
                            <th>Parameter Metrik</th>
                            <th>V3 (2-Lapis Gabungan)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="param-name">Jumlah node / edge</td>
                            <td class="param-val">{len(nodes)} / {len(edges)}</td>
                        </tr>
                        <tr>
                            <td class="param-name">Chunk teks</td>
                            <td class="param-val">55 chunks</td>
                        </tr>
                        <tr>
                            <td class="param-name">SIUP/SIPI/SIKPI/ZEEI/PNBP</td>
                            <td class="param-val">5 / 5</td>
                        </tr>
                        <tr>
                            <td class="param-name">Node terisolasi (komponen)</td>
                            <td class="param-val">9 (10 komp)</td>
                        </tr>
                        <tr>
                            <td class="param-name">Node sampah / placeholder</td>
                            <td class="param-val">2 node</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Vis Network Canvas -->
        <div id="network"></div>

        <!-- Node Details Panel -->
        <div class="info-panel" id="infoPanel">
            <div class="info-header">
                <h2 id="nodeTitle">Nama Node</h2>
                <button class="close-btn" onclick="closePanel()">&times;</button>
            </div>
            <div class="info-section">
                <label>Kategori & Lapisan</label>
                <div class="value">
                    <span id="nodeTypeTag" class="tag-pill" style="background: #0284C7;">konsep</span>
                    <span id="nodeLayerTag" class="tag-pill" style="background: #334155;">Lapisan 2</span>
                </div>
            </div>
            <div class="info-section" id="eliSection" style="display:none;">
                <label>Identifikasi Norma (ELI / Versi ID)</label>
                <div class="value" id="nodeEli"></div>
            </div>
            <div class="info-section">
                <label>Deskripsi Yuridis</label>
                <div class="value" id="nodeDesc">Tidak ada deskripsi teks.</div>
            </div>
            <div class="info-section">
                <label>Relasi Terhubung (<span id="relCount">0</span>)</label>
                <div id="relList" style="max-height: 160px; overflow-y: auto;"></div>
            </div>
        </div>
    </div>

    <script type="text/javascript">
        const allNodes = {nodes_json};
        const allEdges = {edges_json};

        let nodesDataSet = new vis.DataSet(allNodes);
        let edgesDataSet = new vis.DataSet(allEdges);

        const container = document.getElementById("network");
        const data = {{ nodes: nodesDataSet, edges: edgesDataSet }};

        const options = {{
            nodes: {{
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                width: 1.2,
                smooth: {{
                    type: "continuous"
                }},
                selectionWidth: 3
            }},
            physics: {{
                stabilization: {{
                    enabled: true,
                    iterations: 120,
                    updateInterval: 25
                }},
                barnesHut: {{
                    gravitationalConstant: -3500,
                    centralGravity: 0.35,
                    springLength: 95,
                    springConstant: 0.04,
                    damping: 0.09
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100,
                navigationButtons: false,
                keyboard: false
            }}
        }};

        const network = new vis.Network(container, data, options);
        let isPhysicsEnabled = true;

        network.on("stabilizationIterationsDone", function () {{
            network.setOptions({{ physics: false }});
            isPhysicsEnabled = false;
            document.getElementById("physicsBtn").innerText = "▶ Simulasi Gravitasi";
        }});

        function togglePhysics() {{
            isPhysicsEnabled = !isPhysicsEnabled;
            network.setOptions({{ physics: isPhysicsEnabled }});
            document.getElementById("physicsBtn").innerText = isPhysicsEnabled ? "⏸ Bekukan Posisi" : "▶ Simulasi Gravitasi";
        }}

        // Klik Node untuk Membuka Detail Panel
        network.on("click", function (params) {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const node = allNodes.find(n => n.id === nodeId);
                if (node) {{
                    showNodeDetails(node);
                }}
            }} else {{
                closePanel();
            }}
        }});

        function showNodeDetails(node) {{
            document.getElementById("nodeTitle").innerText = node.full_name;
            const typeTag = document.getElementById("nodeTypeTag");
            typeTag.innerText = node.group;
            typeTag.style.background = node.color.background;

            document.getElementById("nodeLayerTag").innerText = "Lapisan " + node.lapisan;
            document.getElementById("nodeDesc").innerText = node.description || "(Deskripsi tidak tersedia dalam naskah chunk)";

            const eliSec = document.getElementById("eliSection");
            const eliVal = document.getElementById("nodeEli");
            if (node.eli_id || node.versi_id) {{
                eliSec.style.display = "block";
                eliVal.innerText = node.eli_id || node.versi_id;
            }} else {{
                eliSec.style.display = "none";
            }}

            const connectedEdges = allEdges.filter(e => e.from === node.id || e.to === node.id);
            document.getElementById("relCount").innerText = connectedEdges.length;

            let relHtml = "";
            connectedEdges.forEach(e => {{
                const isOut = e.from === node.id;
                const otherNode = isOut ? e.to : e.from;
                const arrow = isOut ? "→" : "←";
                relHtml += `<div class="rel-item">
                    <strong style="color:#38BDF8;">${{arrow}} ${{e.relasi || 'relasi'}}</strong>: ${{otherNode}}
                </div>`;
            }});
            document.getElementById("relList").innerHTML = relHtml || "<div style='font-size:11px;color:#94A3B8;'>Tidak ada relasi terhubung.</div>";

            document.getElementById("infoPanel").classList.add("visible");
        }}

        function closePanel() {{
            document.getElementById("infoPanel").classList.remove("visible");
        }}

        // Fitur Pindah Posisi Pojok Tabel Metrik (Top-Right -> Bottom-Right -> Bottom-Left)
        let cornerIdx = 0;
        const cornerClasses = ["", "bottom-right", "bottom-left"];
        function toggleCornerPos() {{
            const overlay = document.getElementById("metricsOverlay");
            cornerClasses.forEach(c => c && overlay.classList.remove(c));
            cornerIdx = (cornerIdx + 1) % cornerClasses.length;
            if (cornerClasses[cornerIdx]) {{
                overlay.classList.add(cornerClasses[cornerIdx]);
            }}
        }}

        // Fitur Minimize Tabel Metrik
        let isTableHidden = false;
        function toggleTableVisibility() {{
            isTableHidden = !isTableHidden;
            document.getElementById("tableContent").style.display = isTableHidden ? "none" : "block";
            document.getElementById("toggleTblBtn").innerText = isTableHidden ? "+" : "−";
        }}

        // Filter Lapisan (Semua, 1, atau 2)
        let activeLapisan = "all";
        let activeGroups = new Set(allNodes.map(n => n.group));

        function filterLapisan(layer, elem) {{
            document.querySelectorAll(".layer-tab").forEach(t => t.classList.remove("active"));
            elem.classList.add("active");
            activeLapisan = layer;
            applyFilters();
        }}

        function toggleGroup(grp, elem) {{
            if (activeGroups.has(grp)) {{
                activeGroups.delete(grp);
                elem.classList.remove("active");
                elem.classList.add("inactive");
            }} else {{
                activeGroups.add(grp);
                elem.classList.add("active");
                elem.classList.remove("inactive");
            }}
            applyFilters();
        }}

        function applyFilters() {{
            const filteredNodes = allNodes.filter(n => {{
                const matchLayer = (activeLapisan === "all") || (n.lapisan === activeLapisan);
                const matchGroup = activeGroups.has(n.group);
                return matchLayer && matchGroup;
            }});

            const validNodeIds = new Set(filteredNodes.map(n => n.id));
            const filteredEdges = allEdges.filter(e => validNodeIds.has(e.from) && validNodeIds.has(e.to));

            nodesDataSet.clear();
            edgesDataSet.clear();
            nodesDataSet.add(filteredNodes);
            edgesDataSet.add(filteredEdges);
        }}

        // Pencarian Cepat
        function searchNode(event) {{
            const query = event.target.value.toLowerCase().trim();
            if (!query) return;

            const found = allNodes.find(n => n.full_name.toLowerCase().includes(query));
            if (found) {{
                network.focus(found.id, {{
                    scale: 1.2,
                    animation: {{
                        duration: 800,
                        easingFunction: "easeInOutQuad"
                    }}
                }});
                network.selectNodes([found.id]);
                showNodeDetails(found);
            }}
        }}
    </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"[SUKSES] Visualisasi HTML interaktif berhasil dibuat di: {output_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graphml", default="7_indexing_regulasi_2lapis/5_penautan_graf_gabungan/hasil/gabungan.graphml")
    ap.add_argument("--out", default="7_indexing_regulasi_2lapis/6_evaluasi_dan_laporan/hasil/visualisasi_graf_gabungan.html")
    ap.add_argument("--title", default="Visualisasi Graf Pengetahuan Regulasi (2-Lapis)")
    args = ap.parse_args()

    print(f"Membaca file GraphML dari: {args.graphml} ...")
    nodes, edges = parse_graphml(args.graphml)
    print(f"Total node diparsing: {len(nodes)} | Total edge: {len(edges)}")
    generate_html(nodes, edges, args.out, args.title)


if __name__ == "__main__":
    main()
