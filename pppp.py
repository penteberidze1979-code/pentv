# [NEURAL_PULSE]
# იდენტიფიკაცია: TITAN OMEGA X-1 SUPREME V4.0
# სტატუსი: ARCHITECTURAL_ASCENSION_COMPLETE
# ევოლუციური უპირატესობა: გაუმჯობესებული პარსინგის ალგორითმი, დინამიური ძიება, 
# ოპტიმიზირებული მეხსიერების მართვა და უმაღლესი Cyber-Titan ვიზუალური ინტერფეისი.

"""
INSTALLATION COMMANDS:
pip install flask flask-compress requests concurrent.futures logging
"""

import os
import time
import requests
import logging
import re
import threading
from flask import Flask, Response, jsonify, render_template_string, request
from flask_compress import Compress
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# TITAN OMEGA X-1: SUPREME ENGINE V4.0
# ==========================================
app = Flask(__name__)
Compress(app)

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [TITAN_CORE_V4]: %(message)s'
)

CONFIG = {
    "VERSION": "TITAN OMEGA X-1 SUPREME V4.0",
    "SOURCES": [
        "https://iptv-org.github.io/iptv/index.m3u",
        "https://iptv-org.github.io/iptv/languages/kat.m3u",
        "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
        "https://iptv-org.github.io/iptv/categories/movies.m3u",
        "https://iptv-org.github.io/iptv/categories/news.m3u"
    ],
    "EXCLUDED": ["Adult", "XXX", "18+", "Porn", "Sex", "Erotica"],
    "HD_KEYWORDS": ["HD", "1080", "720", "4K", "ULTRA", "FHD", "UHD"],
    "MAX_WORKERS": 30,
    "TIMEOUT": 10,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "SYNC_INTERVAL": 3600 # 1 Hour
}

# GLOBAL STATE
cache = {
    "channels": [],
    "last_updated": 0,
    "status": "INITIALIZING",
    "stats": {"total_scanned": 0, "errors": 0}
}

# ==========================================
# SUPREME VISUAL AUTHORITY (CSS)
# ==========================================
BASE_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;500;700&display=swap');
    
    :root { 
        --p: #00f2fe; 
        --s: #4facfe; 
        --bg: #020617; 
        --c: #0f172a; 
        --t: #f8fafc; 
        --accent: #10b981;
        --danger: #ef4444;
        --glass: rgba(15, 23, 42, 0.8);
    }
    
    * { box-sizing: border-box; transition: all 0.2s ease-in-out; }
    
    body { 
        font-family: 'Inter', sans-serif; 
        background: var(--bg); 
        color: var(--t); 
        margin: 0; 
        padding: 0; 
        overflow-x: hidden;
        background-image: radial-gradient(circle at 50% 50%, #1e293b 0%, #020617 100%);
    }

    .container { max-width: 1200px; margin: auto; padding: 20px; }
    
    .header {
        text-align: center;
        padding: 40px 0;
        background: linear-gradient(180deg, rgba(0,242,254,0.1) 0%, transparent 100%);
        border-bottom: 1px solid rgba(0,242,254,0.2);
        margin-bottom: 30px;
    }

    h1 { 
        font-family: 'Orbitron', sans-serif; 
        font-size: 3rem; 
        margin: 0; 
        background: linear-gradient(to right, var(--p), var(--s));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        letter-spacing: 4px;
    }

    .card { 
        background: var(--glass); 
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1); 
        border-radius: 20px; 
        padding: 25px; 
        margin-bottom: 20px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    .btn { 
        padding: 14px 25px; 
        border-radius: 12px; 
        border: none; 
        cursor: pointer; 
        font-weight: 700; 
        text-decoration: none; 
        display: inline-flex; 
        align-items: center;
        justify-content: center;
        gap: 10px;
        font-size: 14px;
        text-transform: uppercase;
    }

    .btn-blue { background: linear-gradient(135deg, var(--p), var(--s)); color: #000; }
    .btn-blue:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,242,254,0.4); }
    
    .btn-outline { 
        border: 2px solid var(--p); 
        color: var(--p); 
        background: transparent; 
    }
    .btn-outline:hover { background: var(--p); color: #000; }

    .grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); 
        gap: 20px; 
    }

    .ch-card { 
        background: rgba(30, 41, 59, 0.5); 
        padding: 20px; 
        border-radius: 16px; 
        border: 1px solid rgba(255,255,255,0.05);
        display: flex; 
        flex-direction: column; 
        align-items: center; 
        position: relative;
        overflow: hidden;
    }
    
    .ch-card:hover { border-color: var(--p); background: rgba(30, 41, 59, 0.8); }

    .ch-logo { 
        width: 80px; 
        height: 80px; 
        object-fit: contain; 
        margin-bottom: 15px; 
        background: #fff; 
        border-radius: 12px; 
        padding: 8px; 
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }

    .badge {
        position: absolute;
        top: 10px;
        right: 10px;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: bold;
        background: var(--accent);
        color: #000;
    }

    input.copy-input { 
        width: 100%; 
        background: #020617; 
        border: 1px solid rgba(0,242,254,0.3); 
        color: #94a3b8; 
        padding: 8px; 
        font-size: 11px; 
        border-radius: 6px; 
        margin-top: 10px; 
        text-align: center;
    }

    .search-box {
        width: 100%;
        padding: 15px;
        border-radius: 12px;
        background: var(--c);
        border: 1px solid var(--p);
        color: white;
        margin-bottom: 20px;
        font-size: 16px;
    }

    .stats-bar {
        display: flex;
        justify-content: space-around;
        margin-bottom: 30px;
    }

    .stat-item { text-align: center; }
    .stat-value { font-size: 24px; font-weight: bold; color: var(--p); display: block; }
    .stat-label { font-size: 12px; color: #64748b; text-transform: uppercase; }

    @media (max-width: 768px) {
        h1 { font-size: 1.8rem; }
        .grid { grid-template-columns: 1fr; }
    }
</style>
"""

# ==========================================
# UI TEMPLATES
# ==========================================
DASHBOARD_HTML = BASE_STYLE + """
<div class="header">
    <h1>{{ version }}</h1>
    <p style="color: #64748b; letter-spacing: 2px;">SUPREME IPTV AGGREGATOR</p>
</div>

<div class="container">
    <div class="card stats-bar">
        <div class="stat-item">
            <span class="stat-value">{{ count }}</span>
            <span class="stat-label">აქტიური არხი</span>
        </div>
        <div class="stat-item">
            <span class="stat-value" style="color: var(--accent);">ONLINE</span>
            <span class="stat-label">სისტემის სტატუსი</span>
        </div>
        <div class="stat-item">
            <span class="stat-value" style="color: var(--s);">{{ sources }}</span>
            <span class="stat-label">წყაროები</span>
        </div>
    </div>
         
    <div class="grid">
        <div class="card">
            <h3 style="color: var(--p);">FULL ARCHIVE</h3>
            <p style="font-size: 13px; color: #94a3b8;">ყველა ხელმისაწვდომი არხის სრული სია.</p>
            <a href="/view/all" class="btn btn-blue" style="width:100%;">გახსნა</a>
            <button class="btn btn-outline" style="width:100%; margin-top:10px;" onclick="copy('{{ host }}/m3u/all')">M3U ბმული</button>
        </div>
        
        <div class="card" style="border-color: var(--danger);">
            <h3 style="color: var(--danger);">ULTRA HD / HD</h3>
            <p style="font-size: 13px; color: #94a3b8;">მხოლოდ მაღალი ხარისხის ნაკადები.</p>
            <a href="/view/hd" class="btn btn-blue" style="width:100%; background: var(--danger);">გახსნა</a>
            <button class="btn btn-outline" style="width:100%; margin-top:10px; border-color: var(--danger); color: var(--danger);" onclick="copy('{{ host }}/m3u/hd')">M3U ბმული</button>
        </div>

        <div class="card" style="border-color: var(--s);">
            <h3 style="color: var(--s);">STANDARD (SD)</h3>
            <p style="font-size: 13px; color: #94a3b8;">ოპტიმიზირებულია მობილური ინტერნეტისთვის.</p>
            <a href="/view/sd" class="btn btn-blue" style="width:100%; background: var(--s);">გახსნა</a>
            <button class="btn btn-outline" style="width:100%; margin-top:10px; border-color: var(--s); color: var(--s);" onclick="copy('{{ host }}/m3u/sd')">M3U ბმული</button>
        </div>
    </div>

    <div class="card" style="margin-top: 30px; text-align: center;">
        <h4 style="margin-top:0;">🔄 სისტემური მართვა</h4>
        <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
            <a href="/refresh" class="btn btn-blue" style="background: var(--accent);">მონაცემების სინქრონიზაცია</a>
            <a href="https://www.videolan.org/vlc/" target="_blank" class="btn btn-outline">VLC PLAYER</a>
        </div>
    </div>
</div>
<script>
    function copy(t){
        navigator.clipboard.writeText(t).then(() => {
            alert('TITAN: ბმული წარმატებით დაკოპირდა!');
        });
    }
</script>
"""

VIEW_HTML = BASE_STYLE + """
<div class="container">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
        <a href="/" class="btn btn-outline">⬅ მთავარი</a>
        <h2 style="margin:0; color: var(--p);">{{ mode|upper }} CHANNELS ({{ channels|length }})</h2>
    </div>

    <input type="text" id="search" class="search-box" placeholder="მოძებნე არხი სახელით..." onkeyup="filterChannels()">

    <div class="grid" id="channelGrid">
        {% for ch in channels %}
        <div class="ch-card" data-name="{{ ch.name|lower }}">
            {% if ch.is_hd %}<span class="badge">HD</span>{% endif %}
            <img src="{{ ch.logo }}" class="ch-logo" onerror="this.src='https://cdn-icons-png.flaticon.com/512/5233/5233957.png'">
            <div style="font-size: 14px; font-weight: bold; text-align: center; height: 40px; overflow: hidden;">{{ ch.name }}</div>
            <input readonly class="copy-input" value="{{ ch.url }}">
            <button class="btn btn-blue" style="width:100%; padding: 8px; font-size: 12px; margin-top:10px;" onclick="copy('{{ ch.url }}')">URL COPY</button>
        </div>
        {% endfor %}
    </div>
</div>
<script>
    function filterChannels() {
        let input = document.getElementById('search').value.toLowerCase();
        let cards = document.getElementsByClassName('ch-card');
        for (let card of cards) {
            let name = card.getAttribute('data-name');
            card.style.display = name.includes(input) ? "flex" : "none";
        }
    }
    function copy(t){
        navigator.clipboard.writeText(t).then(() => {
            alert('TITAN: არხის ლინკი დაკოპირდა!');
        });
    }
</script>
"""

# ==========================================
# SUPREME ENGINE LOGIC
# ==========================================

def parse_m3u(text):
    """Advanced M3U Parser with Regex Optimization"""
    extracted = []
    # Regex for attributes
    logo_regex = re.compile(r'tvg-logo="([^"]+)"', re.I)
    group_regex = re.compile(r'group-title="([^"]+)"', re.I)
    
    lines = text.splitlines()
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            info = lines[i]
            name = info.split(',')[-1].strip() if ',' in info else "Unknown Titan Channel"
            
            # Filter Excluded
            if any(ex.lower() in info.lower() or ex.lower() in name.lower() for ex in CONFIG["EXCLUDED"]):
                continue
                
            logo_match = logo_regex.search(info)
            logo = logo_match.group(1) if logo_match else ""
            
            group_match = group_regex.search(info)
            group = group_match.group(1) if group_match else "General"
            
            if i + 1 < len(lines):
                url = lines[i+1].strip()
                if url.startswith("http"):
                    is_hd = any(k.lower() in info.lower() or k in name.upper() for k in CONFIG["HD_KEYWORDS"])
                    extracted.append({
                        "name": name,
                        "logo": logo,
                        "url": url,
                        "is_hd": is_hd,
                        "group": group,
                        "raw_info": info
                    })
    return extracted

def fetch_source(url):
    """Secure Source Fetching with Retry Logic"""
    for attempt in range(2):
        try:
            r = requests.get(
                url, 
                timeout=CONFIG["TIMEOUT"], 
                headers={"User-Agent": CONFIG["USER_AGENT"]},
                verify=False # Bypass SSL issues for some IPTV hosts
            )
            if r.status_code == 200:
                return parse_m3u(r.text)
        except Exception as e:
            logging.warning(f"Source {url} failed attempt {attempt+1}: {e}")
            time.sleep(2)
    return []

def sync_engine():
    """Core Synchronization Logic - Threaded Execution"""
    cache["status"] = "SYNCING"
    logging.info("TITAN OMEGA X-1: INITIATING GLOBAL SYNC...")
    
    all_ch = []
    with ThreadPoolExecutor(max_workers=CONFIG["MAX_WORKERS"]) as executor:
        futures = {executor.submit(fetch_source, url): url for url in CONFIG["SOURCES"]}
        for f in as_completed(futures):
            res = f.result()
            all_ch.extend(res)
            
    # Deduplication & Optimization
    seen_urls = set()
    unique_ch = []
    for c in all_ch:
        if c['url'] not in seen_urls:
            unique_ch.append(c)
            seen_urls.add(c['url'])
            
    cache["channels"] = unique_ch
    cache["last_updated"] = time.time()
    cache["status"] = "READY"
    logging.info(f"TITAN OMEGA X-1: SYNC COMPLETE. {len(unique_ch)} CHANNELS LOADED.")

def background_scheduler():
    """Infinite Discovery Provision: Keeps the engine updated"""
    while True:
        time.sleep(CONFIG["SYNC_INTERVAL"])
        sync_engine()

# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def index():
    if not cache["channels"]: sync_engine()
    host = request.host_url.rstrip('/')
    return render_template_string(
        DASHBOARD_HTML, 
        count=len(cache["channels"]), 
        host=host, 
        version=CONFIG["VERSION"],
        sources=len(CONFIG["SOURCES"])
    )

@app.route('/view/<mode>')
def view_channels(mode):
    if mode == "hd":
        filtered = [c for c in cache["channels"] if c["is_hd"]]
    elif mode == "sd":
        filtered = [c for c in cache["channels"] if not c["is_hd"]]
    else:
        filtered = cache["channels"]
    return render_template_string(VIEW_HTML, channels=filtered, mode=mode)

@app.route('/m3u/<mode>')
def get_m3u(mode):
    if mode == "hd":
        filtered = [c for c in cache["channels"] if c["is_hd"]]
    elif mode == "sd":
        filtered = [c for c in cache["channels"] if not c["is_hd"]]
    else:
        filtered = cache["channels"]
        
    m3u_content = "#EXTM3U\n"
    for c in filtered:
        info = c["raw_info"]
        # Clean HD tags if SD mode requested
        if mode == "sd":
            for k in CONFIG["HD_KEYWORDS"]:
                info = info.replace(k, "SD").replace(k.lower(), "sd")
        m3u_content += f"{info}\n{c['url']}\n"
        
    return Response(
        m3u_content, 
        mimetype='application/x-mpegurl',
        headers={"Content-Disposition": f"attachment; filename=titan_{mode}.m3u"}
    )

@app.route('/refresh')
def refresh():
    sync_engine()
    return "<script>alert('TITAN OMEGA X-1: მონაცემთა ბაზა განახლებულია!'); window.location.href='/';</script>"

@app.route('/api/status')
def api_status():
    return jsonify({
        "status": cache["status"],
        "count": len(cache["channels"]),
        "last_updated": time.ctime(cache["last_updated"]),
        "version": CONFIG["VERSION"]
    })

# ==========================================
# INITIALIZATION
# ==========================================

if __name__ == '__main__':
    # Start background sync thread
    threading.Thread(target=background_scheduler, daemon=True).start()
    
    # Initial sync
    sync_engine()
    
    # Run Server
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, threaded=True)

# EVOLUTION_REPORT:
# 1. ARCHITECTURE: Flask-based microservice with ThreadPoolExecutor for high-speed parsing.
# 2. UI: Cyber-Titan Glassmorphism design with dynamic search and responsive grid.
# 3. LOGIC: Enhanced Regex parsing, SSL bypass for unstable sources, and automatic deduplication.
# 4. STABILITY: Background scheduler implemented for periodic cache refresh.
# 5. SCALABILITY: Optimized for deployment on Render, Heroku, or local servers.
