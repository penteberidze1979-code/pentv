import requests
import asyncio
import aiohttp
import re
import os
import time
import json
import psutil
import random
import gzip
import sys
import socket
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, Response
from flask_cors import CORS

# --- CONFIGURATION ---
class Config:
    APP_PORT = 10000  # Render-ისთვის ხშირად 10000 გამოიყენება
    SD_KEYWORDS = ["sd", "480p", "360p", "240p", "low", "medium", "lite", "smooth", "eco", "basic", "standard"]
    HD_KEYWORDS = ["hd", "1080p", "720p", "fhd", "4k", "uhd", "high", "ultra"]
    GLOBAL_SOURCES = [
        "https://iptv-org.github.io/iptv/languages/kat.m3u",
        "https://iptv-org.github.io/iptv/languages/rus.m3u",
        "https://iptv-org.github.io/iptv/index.m3u",
        "https://raw.githubusercontent.com/LITUATUI/IPTV/main/GE.m3u"
    ]
    UA_POOL = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
    ]
    CONCURRENCY_LIMIT = 500

# --- UI TEMPLATE (HTML) ---
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ka">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TITAN OMEGA X-1 | V12 SUPREME</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Noto+Sans+Georgian:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --neon: #00f2ff; --bg: #020205; --panel: #0a0a1a; --text: #e0e0e0; --success: #00ff88; --danger: #ff2d55; --warning: #ffcc00; }
        body { background: var(--bg); color: var(--text); font-family: 'Noto Sans Georgian', sans-serif; margin: 0; padding: 10px; overflow-x: hidden; }
        .box { border: 1px solid rgba(0,242,255,0.2); background: var(--panel); padding: 15px; border-radius: 12px; margin-bottom: 15px; position: relative; box-shadow: 0 0 20px rgba(0,242,255,0.05); }
        h2 { color: var(--neon); text-align: center; font-family: 'Orbitron'; letter-spacing: 2px; text-shadow: 0 0 10px var(--neon); margin-top: 0; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; text-align: center; margin-bottom: 15px; }
        .stat-val { font-size: 16px; color: var(--success); font-weight: bold; }
        textarea, input { width: 100%; background: #000; color: var(--neon); border: 1px solid #1a1a3a; padding: 12px; margin: 8px 0; border-radius: 8px; box-sizing: border-box; font-family: monospace; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 10px; }
        button { width: 100%; background: var(--neon); color: #000; padding: 12px; border: none; font-weight: 900; border-radius: 8px; cursor: pointer; text-transform: uppercase; transition: 0.3s; font-size: 12px; }
        button:hover { background: #fff; box-shadow: 0 0 15px var(--neon); }
        .btn-sd { background: var(--warning); }
        .btn-hd { background: var(--neon); }
        .btn-all { background: var(--success); }
        .logs { height: 120px; overflow-y: auto; background: #000; padding: 10px; font-size: 10px; color: var(--success); border-radius: 8px; border: 1px solid #111; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: var(--neon); }
        .health-panel { font-size: 10px; margin-top: 10px; border-top: 1px solid #1a1a3a; padding-top: 10px; display: flex; justify-content: space-between; }
    </style>
</head>
<body>
    <div class="box">
        <h2>TITAN OMEGA X-1</h2>
        <div class="grid">
            <div><div id="st">...</div><div style="font-size:9px">STATUS</div></div>
            <div><div class="stat-val" id="nc">0</div><div style="font-size:9px">NODES</div></div>
            <div><div class="stat-val" id="cpu">0%</div><div style="font-size:9px">CPU</div></div>
            <div><div class="stat-val" id="ram">0%</div><div style="font-size:9px">RAM</div></div>
        </div>
        <input type="text" id="url" placeholder="Enter M3U Link or Search Query...">
        <div class="btn-group">
            <button class="btn-sd" onclick="uiAction('sd')">SCAN SD</button>
            <button class="btn-hd" onclick="uiAction('hd')">SCAN HD</button>
            <button class="btn-all" onclick="uiAction('all')">SCAN ALL</button>
        </div>
        <button onclick="process()">INITIATE DEEP SCAN</button>
    </div>
    <div class="box">
        <textarea id="res" rows="8" readonly placeholder="Awaiting Neural Input..."></textarea>
        <button onclick="copyLink()" style="background: var(--success); margin-top:10px">EXPORT COPYABLE LINK</button>
    </div>
    <div class="box">
        <div class="logs" id="lb"></div>
        <div class="health-panel">
            <span>CORE: ACTIVE</span>
            <span id="uptime">UPTIME: 00:00:00</span>
            <span>V12 EVO</span>
        </div>
    </div>
    <script>
        async function update() {
            try {
                const r = await fetch('/status');
                const d = await r.json();
                document.getElementById('st').innerText = d.status;
                document.getElementById('nc').innerText = d.diag.nodes;
                document.getElementById('cpu').innerText = d.diag.cpu;
                document.getElementById('ram').innerText = d.diag.ram;
                document.getElementById('uptime').innerText = "UPTIME: " + d.diag.uptime;
                document.getElementById('lb').innerHTML = d.logs.map(l => `<div>${l}</div>`).reverse().join('');
            } catch(e) {}
        }
        setInterval(update, 3000);
        async function process() {
            const u = document.getElementById('url').value;
            if(!u) return;
            document.getElementById('res').value = "⚡ INITIATING DEEP SCAN...";
            const r = await fetch('/process', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u, mode: 'all'}) });
            const d = await r.json();
            document.getElementById('res').value = d.result;
        }
        async function uiAction(mode) {
            const u = document.getElementById('url').value || "GLOBAL_SCAN";
            document.getElementById('res').value = `⚡ UI_CONTROLLER: RENDER_${mode.toUpperCase()}_ACTION...`;
            const r = await fetch('/process', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u, mode: mode}) });
            const d = await r.json();
            document.getElementById('res').value = d.result;
        }
        function copyLink() {
            const text = document.getElementById('res').value;
            const linkMatch = text.match(/https?:\\/\\/[^\\s]+/);
            if(linkMatch) {
                navigator.clipboard.writeText(linkMatch[0]);
                alert("ClipboardProvider: Link Exported!");
            } else {
                document.getElementById('res').select();
                document.execCommand('copy');
                alert("ClipboardProvider: Full Manifest Exported!");
            }
        }
    </script>
</body>
</html>
"""

# --- LOGIC CLASSES ---
class SourceManager:
    @staticmethod
    async def fetch_raw_payload(session, url):
        headers = {'User-Agent': random.choice(Config.UA_POOL)}
        try:
            async with session.get(url, headers=headers, timeout=10) as r:
                if r.status == 200:
                    content = await r.read()
                    if r.headers.get('Content-Encoding') == 'gzip' or content.startswith(b'\\x1f\\x8b'):
                        return gzip.decompress(content).decode('utf-8', errors='ignore')
                    return content.decode('utf-8', errors='ignore')
        except: return ""
        return ""

class GlobalScanner:
    @staticmethod
    async def initiate_deep_scan(session, url):
        payload = await SourceManager.fetch_raw_payload(session, url)
        found = re.findall(r'#EXTINF:.*?,(.*?)\\n(http[s]?://[^\\s]+)', payload)
        return [{"name": name.strip(), "url": link.strip()} for name, link in found]

class QualityEngine:
    @staticmethod
    def filter_sd_streams(nodes):
        return [n for n in nodes if any(k in n['url'].lower() or k in n['name'].lower() for k in Config.SD_KEYWORDS)]
    @staticmethod
    def filter_hd_streams(nodes):
        return [n for n in nodes if any(k in n['url'].lower() or k in n['name'].lower() for k in Config.HD_KEYWORDS)]

class StreamProcessor:
    @staticmethod
    def downscale_to_sd_logic(url):
        return url.replace("1080", "480").replace("720", "480").replace("FHD", "SD").replace("HD", "SD")

class IdentityManager:
    @staticmethod
    def assign_group_by_country(name):
        name = name.upper()
        if any(x in name for x in ['GE', 'GEO', 'KA', 'ქართული']): return "GEORGIAN"
        if any(x in name for x in ['RU', 'RUS', 'РОССიЯ']): return "RUSSIAN"
        return "INTERNATIONAL"

class OutputEngine:
    @staticmethod
    def generate_self_updating_manifest(nodes):
        m3u = ["#EXTM3U"]
        for n in nodes:
            grp = IdentityManager.assign_group_by_country(n['name'])
            m3u.append(f'#EXTINF:-1 group-title="{grp}",{n["name"]}')
            m3u.append(n['url'])
        return "\\n".join(m3u)

class TitanCore:
    def __init__(self):
        self.global_db = []
        self.logs = []
        self.health_status = "INIT"
        self.start_time = datetime.now()

    def log(self, msg, level="INFO"):
        t = datetime.now().strftime("%H:%M:%S")
        entry = f"💠 [{level}] [{t}] {msg}"
        self.logs.append(entry)
        if len(self.logs) > 100: self.logs.pop(0)
        print(entry)

    def get_diagnostics(self):
        try: cpu, ram = f"{psutil.cpu_percent()}%", f"{psutil.virtual_memory().percent}%"
        except: cpu, ram = "N/A", "N/A"
        return {"cpu": cpu, "ram": ram, "uptime": str(datetime.now() - self.start_time).split('.')[0], "nodes": len(self.global_db)}

# --- APP INITIALIZATION ---
core = TitanCore()
app = Flask(__name__)
CORS(app)

async def recursive_update_cycle():
    while True:
        core.health_status = "სკანირება"
        async with aiohttp.ClientSession() as session:
            all_nodes = []
            for src in Config.GLOBAL_SOURCES:
                nodes = await GlobalScanner.initiate_deep_scan(session, src)
                all_nodes.extend(nodes)
            core.global_db = all_nodes
            core.log(f"SelfHealing: Cycle Complete. Nodes: {len(all_nodes)}", "CORE")
        core.health_status = "ოპტიმიზირებული"
        await asyncio.sleep(1800)

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/status')
def status():
    return jsonify({"status": core.health_status, "logs": core.logs, "diag": core.get_diagnostics()})

@app.route('/process', methods=['POST'])
async def handle():
    data = request.json
    user_url = data.get('url', '')
    mode = data.get('mode', 'all')
    core.log(f"UIController: Action {mode.upper()} triggered", "UI_BRIDGE")
    
    async with aiohttp.ClientSession() as session:
        if "http" in user_url:
            nodes = await GlobalScanner.initiate_deep_scan(session, user_url)
        else:
            nodes = core.global_db
            
        if mode == 'sd':
            nodes = QualityEngine.filter_sd_streams(nodes)
            for n in nodes: n['url'] = StreamProcessor.downscale_to_sd_logic(n['url'])
        elif mode == 'hd':
            nodes = QualityEngine.filter_hd_streams(nodes)
            
        if not nodes: return jsonify({"result": "No streams found."})
        
        manifest = OutputEngine.generate_self_updating_manifest(nodes)
        try:
            async with session.post("https://dpaste.org/api/", data={'content': manifest, 'expiry_days': 1}) as r:
                cloud_link = (await r.text()).strip() + "/raw"
        except: cloud_link = "Local Link Only"

        return jsonify({
            "result": f"🚀 TITAN OMEGA: {mode.upper()} SUCCESS\\n"
                      f"------------------------------------------\\n"
                      f"MANIFEST LINK:\\n{cloud_link}\\n"
                      f"------------------------------------------\\n"
                      f"NODES: {len(nodes)} | STATUS: LIVE"
        })

@app.route('/playlist.m3u')
def get_playlist():
    return Response(OutputEngine.generate_self_updating_manifest(core.global_db), mimetype='text/plain')

def run_async_tasks():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(recursive_update_cycle())

if __name__ == '__main__':
    from threading import Thread
    Thread(target=run_async_tasks, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
