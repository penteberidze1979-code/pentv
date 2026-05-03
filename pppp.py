# INSTALLATION: pip install flask flask-cors requests aiohttp psutil flask-compress
# CDN_DEPENDENCIES: https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Noto+Sans+Georgian:wght@400;700&display=swap

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
from flask import Flask, render_template, request, jsonify, Response, abort
from flask_cors import CORS
from flask_compress import Compress
from threading import Thread

# ==========================================
# 1. კონფიგურაცია და ინფრასტრუქტურა
# ==========================================

class Config:
    """სისტემური კონფიგურაცია: უზენაესი პარამეტრების ბირთვი"""
    APP_PORT = int(os.environ.get("PORT", 5000))
    DEBUG = False
    
    SD_KEYWORDS = [
        "sd", "480p", "360p", "240p", "vga", "mobile", "low", "medium", 
        "lite", "smooth", "mini", "eco", "basic", "standard", "fluid",
        "720p", "hd", "georgia", "kat", "rustavi", "imedi", "formula", "maestro",
        "pos-tv", "tv24", "silk", "adjara", "gds", "obiektivi"
    ]
    
    SD_RESOLUTION_LIMITS = ["480x", "640x", "360x", "854x480", "bandwidth=800", "bandwidth=1200", "bandwidth=1500"]
    GEO_TAGS = ["ge", "ka", "ru", "en", "us", "uk", "fr", "de", "it"]

    GLOBAL_SOURCES = [
        "https://iptv-org.github.io/iptv/languages/kat.m3u",
        "https://iptv-org.github.io/iptv/languages/rus.m3u",
        "https://iptv-org.github.io/iptv/languages/eng.m3u",
        "https://iptv-org.github.io/iptv/categories/movies.m3u",
        "https://iptv-org.github.io/iptv/categories/sports.m3u",
        "https://iptv-org.github.io/iptv/index.m3u",
        "https://iptv-org.github.io/iptv/categories/entertainment.m3u",
        "https://iptv-org.github.io/iptv/categories/news.m3u",
        "https://iptv-org.github.io/iptv/categories/music.m3u",
        "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
        "https://raw.githubusercontent.com/LITUATUI/IPTV/main/GE.m3u"
    ]
    
    UA_POOL = [
        "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    ]

    CONCURRENCY_LIMIT = 750
    RECOVERY_DELAY = 3
    CACHE_EXPIRY = 3600

class ExternalUploader:
    """ავტომატური ატვირთვის მოდული სარეზერვო სისტემით"""
    @staticmethod
    async def upload_to_web(content):
        # Method 1: dpaste.org
        try:
            async with aiohttp.ClientSession() as session:
                payload = {'content': content, 'expiry_days': 30}
                async with session.post("https://dpaste.org/api/", data=payload, timeout=8) as r:
                    if r.status == 200:
                        link = await r.text()
                        return link.strip() + "/raw"
        except: pass

        # Method 2: file.io
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('text', content)
                async with session.post("https://file.io/?expires=1w", data=data, timeout=8) as r:
                    if r.status == 200:
                        res = await r.json()
                        return res.get('link')
        except: pass
        return None

# ==========================================
# 2. მონაცემთა დამუშავების ბირთვი (Core Logic)
# ==========================================

class TitanCore:
    """TITAN OMEGA X-1: ცენტრალური ლოგიკური პროცესორი"""
    def __init__(self):
        self.global_sd_db = []
        self.logs = []
        self.health_status = "INITIALIZING"
        self.start_time = datetime.now()
        self.request_count = 0
        self.cache = {}
        self.semaphore = asyncio.Semaphore(Config.CONCURRENCY_LIMIT)

    def log(self, msg, level="INFO"):
        t = datetime.now().strftime("%H:%M:%S")
        entry = f"💠 [{level}] [{t}] {msg}"
        self.logs.append(entry)
        if len(self.logs) > 100: self.logs.pop(0)
        print(entry)

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except: return "127.0.0.1"

    async def traffic_compression_bridge(self, response):
        try:
            content = await response.read()
            if response.headers.get('Content-Encoding') == 'gzip' or content.startswith(b'\x1f\x8b'):
                return gzip.decompress(content).decode('utf-8', errors='ignore')
            return content.decode('utf-8', errors='ignore')
        except: return ""

    async def bandwidth_optimizer(self, session, url):
        if ".m3u8" not in url.lower(): return url
        try:
            async with session.get(url, timeout=5) as r:
                if r.status == 200:
                    text = await self.traffic_compression_bridge(r)
                    lines = text.split('\n')
                    best_variant = None
                    min_bw = float('inf')
                    for i, line in enumerate(lines):
                        if "BANDWIDTH" in line:
                            bw_match = re.search(r'BANDWIDTH=(\d+)', line)
                            if bw_match:
                                bw = int(bw_match.group(1))
                                if bw < min_bw:
                                    min_bw = bw
                                    for j in range(i+1, len(lines)):
                                        if lines[j].strip() and not lines[j].startswith("#"):
                                            best_variant = lines[j].strip()
                                            break
                    if best_variant:
                        if not best_variant.startswith("http"):
                            base = url.rsplit('/', 1)[0]
                            best_variant = f"{base}/{best_variant}"
                        return best_variant
        except: pass
        return url

    async def check_stream_health(self, session, url):
        try:
            async with session.head(url, timeout=4) as r:
                return r.status in [200, 206, 302]
        except: return False

    async def fetch_and_filter(self, session, url):
        try:
            async with session.get(url, timeout=15) as r:
                if r.status == 200:
                    text = await self.traffic_compression_bridge(r)
                    found = re.findall(r'#EXTINF:.*?,(.*?)\n(http[s]?://[^\s]+)', text)
                    count = 0
                    for name, link in found:
                        name, link = name.strip(), link.strip()
                        if any(k in name.lower() or k in link.lower() for k in Config.SD_KEYWORDS):
                            if not any(d['url'] == link for d in self.global_sd_db):
                                self.global_sd_db.append({"name": name, "url": link})
                                count += 1
                    return count
        except: return 0

    def process_logic(self, filter_type=None):
        if not filter_type: return self.global_sd_db
        ft = filter_type.lower()
        return [ch for ch in self.global_sd_db if ft in ch['name'].lower()]

    def generate_m3u_format(self, channels):
        m3u = ["#EXTM3U"]
        for ch in channels:
            m3u.append(f'#EXTINF:-1,{ch["name"]}')
            m3u.append(ch["url"])
        return "\n".join(m3u)

    async def findStableCore(self):
        """INFINITE_DISCOVERY_PROVISION: უსასრულო ძიების ციკლი"""
        self.log("INFINITE_DISCOVERY_PROVISION ACTIVE", "CORE")
        retry_count = 0
        while True:
            try:
                self.health_status = "SCANNING"
                async with aiohttp.ClientSession(headers={'User-Agent': random.choice(Config.UA_POOL)}) as session:
                    tasks = [self.fetch_and_filter(session, src) for src in Config.GLOBAL_SOURCES]
                    await asyncio.gather(*tasks)
                
                self.health_status = "STABLE"
                retry_count = 0
                await asyncio.sleep(1800)
            except Exception as e:
                retry_count += 1
                backoff = min(300, 3 * (2 ** retry_count))
                self.log(f"CORE ERROR: {str(e)}. RESTART IN {backoff}s", "RECOVERY")
                await asyncio.sleep(backoff)

core = TitanCore()

# ==========================================
# 3. სინქრონიზაცია და მართვა (Engine)
# ==========================================

def sync_engine():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(core.findStableCore())

def start_background():
    thread = Thread(target=sync_engine, daemon=True)
    thread.start()

# ==========================================
# 4. ვებ-ინტერფეისი და მარშრუტები (Routes)
# ==========================================

app = Flask(__name__)
CORS(app)
Compress(app)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="ka">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TITAN OMEGA X-1</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Noto+Sans+Georgian:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --neon: #00f2ff; --bg: #020205; --panel: #0a0a1a; --text: #e0e0e0; --success: #00ff88; }
        body { background: var(--bg); color: var(--text); font-family: 'Noto Sans Georgian', sans-serif; margin: 0; padding: 10px; }
        .box { border: 1px solid rgba(0,242,255,0.2); background: var(--panel); padding: 15px; border-radius: 12px; margin-bottom: 15px; }
        h2 { color: var(--neon); text-align: center; font-family: 'Orbitron'; }
        .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; text-align: center; }
        .val { font-size: 18px; color: var(--success); font-weight: bold; }
        textarea, input { width: 100%; background: #000; color: var(--neon); border: 1px solid #1a1a3a; padding: 12px; margin: 8px 0; border-radius: 8px; box-sizing: border-box; }
        button { width: 100%; background: var(--neon); color: #000; padding: 15px; border: none; font-weight: 900; border-radius: 8px; cursor: pointer; }
        .logs { height: 100px; overflow-y: auto; background: #000; padding: 10px; font-size: 11px; color: var(--success); }
    </style>
</head>
<body>
    <div class="box">
        <h2>TITAN OMEGA X-1</h2>
        <div class="stat-grid">
            <div><div id="st">...</div><div style="font-size:9px">STATUS</div></div>
            <div><div class="val" id="nc">0</div><div style="font-size:9px">NODES</div></div>
            <div><div class="val" id="ip">...</div><div style="font-size:9px">LOCAL IP</div></div>
        </div>
        <input type="text" id="url" placeholder="M3U URL or Search...">
        <button onclick="runScan()">NEURAL SCAN</button>
    </div>
    <div class="box">
        <textarea id="res" rows="8" readonly></textarea>
    </div>
    <div class="box"><div class="logs" id="lb"></div></div>
    <script>
        async function update() {
            const r = await fetch('/status');
            const d = await r.json();
            document.getElementById('st').innerText = d.status;
            document.getElementById('nc').innerText = d.nodes;
            document.getElementById('ip').innerText = d.ip;
            document.getElementById('lb').innerHTML = d.logs.map(l => `<div>${l}</div>`).reverse().join('');
        }
        setInterval(update, 3000);
        async function runScan() {
            const u = document.getElementById('url').value;
            const r = await fetch('/upload_playlist', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: u}) });
            const d = await r.json();
            document.getElementById('res').value = d.result;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return INDEX_HTML

@app.route('/status')
def get_status():
    return jsonify({
        "status": core.health_status,
        "nodes": len(core.global_sd_db),
        "ip": core.get_local_ip(),
        "logs": core.logs
    })

@app.route('/upload_playlist', methods=['POST'])
async def upload_playlist():
    data = request.json
    url = data.get('url')
    if not url: return jsonify({"result": "Error: No URL"})
    
    core.log(f"SCAN REQUEST: {url}", "USER")
    async with aiohttp.ClientSession() as session:
        optimized_list = []
        # Logic to fetch and optimize
        try:
            async with session.get(url, timeout=10) as r:
                text = await core.traffic_compression_bridge(r)
                found = re.findall(r'#EXTINF:.*?,(.*?)\n(http[s]?://[^\s]+)', text)
                for name, link in found[:50]:
                    opt = await core.bandwidth_optimizer(session, link)
                    optimized_list.append({"name": name, "url": opt})
        except: pass
        
        if not optimized_list:
            optimized_list = core.process_logic(url)[:50]
            
        m3u = core.generate_m3u_format(optimized_list)
        cloud = await ExternalUploader.upload_to_web(m3u)
        local = f"http://{core.get_local_ip()}:{Config.APP_PORT}/get_playlist"
        
        return jsonify({
            "result": f"SCAN COMPLETE\nCloud: {cloud or 'N/A'}\nLocal: {local}"
        })

@app.route('/get_playlist')
def get_playlist():
    channels = core.process_logic(request.args.get('filter'))
    return Response(core.generate_m3u_format(channels), mimetype='text/plain')

@app.route('/view_mode')
def view_mode():
    return "TITAN VIEW MODE: ACTIVE"

# ==========================================
# 5. სისტემური გაშვება
# ==========================================

if __name__ == '__main__':
    start_background()
    app.run(host='0.0.0.0', port=Config.APP_PORT, debug=Config.DEBUG, use_reloader=False)
