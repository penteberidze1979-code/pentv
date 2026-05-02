# [TITAN OMEGA X-1] - SUPREME IPTV ENGINE
# INSTALLATION: pip install flask flask-compress requests concurrent.futures

import os
import time
import requests
import logging
import re
from flask import Flask, Response, jsonify, render_template_string
from flask_compress import Compress
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# CORE CONFIGURATION: TITAN PROTOCOL
# ==========================================
app = Flask(__name__)
Compress(app)

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [%(levelname)s] - TITAN_OMEGA_X1: %(message)s'
)

CONFIG = {
    "VERSION": "TITAN OMEGA X-1 SUPREME v2.0",
    "CACHE_TIMEOUT": 14400,
    "SOURCES": [
        "https://iptv-org.github.io/iptv/index.m3u",
        "https://iptv-org.github.io/iptv/languages/kat.m3u",
        "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
    ],
    "EXCLUDED_KEYWORDS": ["Adult", "XXX", "18+", "Porn", "Sex", "Erotica"],
    "HD_KEYWORDS": ["HD", "1080p", "720p", "4K", "ULTRA", "FHD"],
    "MAX_WORKERS": 15,
    "REQUEST_TIMEOUT": 20,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# GLOBAL STATE
cache = {
    "channels": [], # Structured data: [{"info": str, "url": str, "is_hd": bool}]
    "raw_m3u": "",
    "last_updated": 0,
    "total_channels": 0,
    "status": "INITIALIZING",
    "sources_active": 0
}

# ==========================================
# SUPREME VISUAL INTERFACE (CYBER-TITAN)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ka">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TITAN X-1 | SUPREME DASHBOARD</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #00f2fe;
            --secondary: #4facfe;
            --bg-dark: #020617;
            --card-bg: #0f172a;
            --accent: #f59e0b;
            --success: #10b981;
            --text: #f8fafc;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: radial-gradient(circle at center, #1e293b 0%, #020617 100%);
        }
        .titan-container {
            background: var(--card-bg);
            padding: 3rem;
            border-radius: 2rem;
            box-shadow: 0 0 50px rgba(0, 242, 254, 0.15);
            width: 95%;
            max-width: 700px;
            text-align: center;
            border: 1px solid rgba(0, 242, 254, 0.2);
            backdrop-filter: blur(10px);
        }
        h1 {
            font-size: 2.2rem;
            font-weight: 900;
            background: linear-gradient(to right, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
            letter-spacing: 4px;
            text-transform: uppercase;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 2.5rem;
        }
        .stat-box {
            background: rgba(255, 255, 255, 0.03);
            padding: 1.5rem 1rem;
            border-radius: 1.2rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .stat-value {
            display: block;
            font-size: 1.6rem;
            font-weight: 800;
            color: var(--accent);
        }
        .stat-label { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; }
        .action-zone {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        .btn {
            padding: 1rem;
            border-radius: 1rem;
            border: none;
            cursor: pointer;
            font-weight: 700;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.8rem;
            transition: 0.3s;
            font-size: 0.85rem;
        }
        .btn-primary { background: linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%); color: #000; }
        .btn-outline { border: 1px solid var(--primary); color: var(--primary); background: transparent; }
        .btn-hd { background: #ef4444; color: white; }
        .btn-sd { background: #3b82f6; color: white; }
        .btn-refresh { background: var(--success); color: white; grid-column: span 2; }
        .footer { margin-top: 2rem; font-size: 0.75rem; color: #475569; display: flex; justify-content: space-between; }
    </style>
</head>
<body>
    <div class="titan-container">
        <h1><i class="fas fa-bolt"></i> TITAN OMEGA</h1>
        <div class="stats-grid">
            <div class="stat-box"><span class="stat-value">{{ channels }}</span><span class="stat-label">არხები</span></div>
            <div class="stat-box"><span class="stat-value">{{ sources }}</span><span class="stat-label">წყარო</span></div>
            <div class="stat-box"><span class="stat-value" style="color: var(--success);">ACTIVE</span><span class="stat-label">სტატუსი</span></div>
        </div>
        <div class="action-zone">
            <a href="/get_all" class="btn btn-primary"><i class="fas fa-list"></i> ALL M3U</a>
            <button onclick="copyLink()" class="btn btn-outline"><i class="fas fa-copy"></i> COPY LINK</button>
            <a href="/get_hd" class="btn btn-hd"><i class="fas fa-tv"></i> HD ONLY</a>
            <a href="/get_sd" class="btn btn-sd"><i class="fas fa-broadcast-tower"></i> SD ONLY</a>
            <a href="/refresh" class="btn btn-refresh"><i class="fas fa-sync"></i> SYNC ENGINE REFRESH</a>
        </div>
        <div class="footer">
            <span>SYSTEM: OPERATIONAL</span>
            <span>VER: {{ version }}</span>
        </div>
    </div>
    <script>
        function copyLink() {
            const url = window.location.origin + '/get_all';
            navigator.clipboard.writeText(url).then(() => alert('TITAN LINK COPIED!'));
        }
    </script>
</body>
</html>
"""

# ==========================================
# ALGORITHMIC LOGIC: TITAN ENGINE
# ==========================================

def process_data(raw_text):
    """Parses raw M3U text into structured Titan objects."""
    processed = []
    lines = raw_text.splitlines()
    for i in range(len(lines)):
        line = lines[i]
        if line.startswith("#EXTINF"):
            # Filtering logic
            is_excluded = any(k.lower() in line.lower() for k in CONFIG["EXCLUDED_KEYWORDS"])
            if not is_excluded and i + 1 < len(lines):
                url = lines[i+1].strip()
                if url.startswith("http"):
                    is_hd = any(k.lower() in line.lower() for k in CONFIG["HD_KEYWORDS"])
                    processed.append({
                        "info": line,
                        "url": url,
                        "is_hd": is_hd
                    })
    return processed

def fetch_and_process(url):
    """Fetches source and initiates processing."""
    try:
        headers = {"User-Agent": CONFIG["USER_AGENT"]}
        response = requests.get(url, timeout=CONFIG["REQUEST_TIMEOUT"], headers=headers)
        if response.status_code == 200:
            return process_data(response.text)
    except Exception as e:
        logging.error(f"Fetch Error [{url}]: {e}")
    return []

def sync_engine():
    """Orchestrates multi-threaded data synchronization."""
    logging.info("TITAN_ENGINE: Initiating Global Sync...")
    all_structured = []
    active_count = 0
    
    with ThreadPoolExecutor(max_workers=CONFIG["MAX_WORKERS"]) as executor:
        futures = {executor.submit(fetch_and_process, url): url for url in CONFIG["SOURCES"]}
        for future in as_completed(futures):
            result = future.result()
            if result:
                all_structured.extend(result)
                active_count += 1
    
    # Update Cache
    cache["channels"] = all_structured
    cache["total_channels"] = len(all_structured)
    cache["sources_active"] = active_count
    cache["last_updated"] = time.time()
    cache["status"] = "OPERATIONAL"
    
    # Generate Raw M3U for /get_all
    m3u_header = "#EXTM3U x-tvg-url=\"http://itv.com/epg/epg.xml.gz\"\n"
    body = "\n".join([f"{c['info']}\n{c['url']}" for c in all_structured])
    cache["raw_m3u"] = m3u_header + body
    
    logging.info(f"Sync Complete: {cache['total_channels']} channels from {active_count} sources.")

# ==========================================
# API ROUTES: TITAN INTERFACE
# ==========================================

@app.route('/')
def index():
    """Supreme Dashboard."""
    if not cache["channels"]:
        sync_engine()
    return render_template_string(
        HTML_TEMPLATE,
        channels=cache["total_channels"],
        sources=cache["sources_active"],
        version=CONFIG["VERSION"]
    )

@app.route('/get_all')
def get_all():
    """Returns the full optimized M3U."""
    if not cache["raw_m3u"]: sync_engine()
    return Response(cache["raw_m3u"], mimetype='application/x-mpegurl')

@app.route('/get_hd')
def get_hd():
    """Filters and returns only HD channels."""
    hd_channels = [c for c in cache["channels"] if c["is_hd"]]
    m3u = "#EXTM3U\n" + "\n".join([f"{c['info']}\n{c['url']}" for c in hd_channels])
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/get_sd')
def get_sd():
    """Filters and returns only SD channels."""
    sd_channels = [c for c in cache["channels"] if not c["is_hd"]]
    m3u = "#EXTM3U\n" + "\n".join([f"{c['info']}\n{c['url']}" for c in sd_channels])
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/refresh')
def refresh():
    """Manual trigger for sync engine."""
    sync_engine()
    return """<script>alert('TITAN ENGINE REFRESHED'); window.location.href='/';</script>"""

@app.route('/health')
def health_check():
    """Diagnostic endpoint."""
    return jsonify({
        "status": cache["status"],
        "uptime_since_sync": int(time.time() - cache["last_updated"]),
        "total_channels": cache["total_channels"],
        "sources": cache["sources_active"]
    })

# ==========================================
# EXECUTION
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    sync_engine() # Initial Sync
    app.run(host='0.0.0.0', port=port, threaded=True)
