"""
TITAN OMEGA X-1 SUPREME V4.1: ULTIMATE FUSION
IDENTIFICATION: TITAN_OMEGA_SUPREME_V4.1_EVO
STATUS: ALL SYSTEMS OPERATIONAL | LOGIC FULLY INTEGRATED
"""

import os
import time
import requests
import logging
import re
import threading
import json
import gzip
import socket
from flask import Flask, Response, jsonify, render_template_string, request
from flask_compress import Compress
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# CONFIGURATION
# ==========================================
class Config:
    VERSION = "TITAN OMEGA X-1 SUPREME V4.1 (FUSION)"
    SOURCES = [
        "https://iptv-org.github.io/iptv/index.m3u",
        "https://iptv-org.github.io/iptv/languages/kat.m3u",
        "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
        "https://iptv-org.github.io/iptv/categories/movies.m3u",
        "https://raw.githubusercontent.com/LITUATUI/IPTV/main/GE.m3u"
    ]
    EXCLUDED = ["Adult", "XXX", "18+", "Porn", "Sex", "Erotica"]
    SD_KEYWORDS = ["sd", "480p", "360p", "low", "standard", "mobile", "kat", "georgia"]
    HD_KEYWORDS = ["HD", "1080", "720", "4K", "ULTRA", "FHD", "UHD"]
    MAX_WORKERS = 50
    TIMEOUT = 10
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    SYNC_INTERVAL = 3600

# ==========================================
# EXTERNAL UPLOADER (REAL LOGIC)
# ==========================================
class ExternalUploader:
    @staticmethod
    def upload_to_web(content):
        try:
            # Main: dpaste.org
            r = requests.post("https://dpaste.org/api/", data={'content': content, 'expiry_days': 30}, timeout=8)
            if r.status_code == 200:
                return r.text.strip() + "/raw"
        except:
            return None

# ==========================================
# TITAN CORE ENGINE (FULLY INTEGRATED)
# ==========================================
class TitanCore:
    @staticmethod
    def log(msg, level="info"):
        fmt = f"💠 [TITAN_CORE]: {msg}"
        if level == "info": logging.info(fmt)
        else: logging.warning(fmt)

    @staticmethod
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    @staticmethod
    def traffic_compression_bridge(response):
        content = response.content
        if content.startswith(b'\x1f\x8b'): # Gzip Magic Number
            try:
                return gzip.decompress(content).decode('utf-8', errors='ignore')
            except: pass
        return response.text

    @staticmethod
    def bandwidth_optimizer(url):
        # რეზოლუციის ოპტიმიზაცია URL-ის დონეზე
        if "1080" in url: url = url.replace("1080", "480")
        if "720" in url: url = url.replace("720", "480")
        return url

    @staticmethod
    def fetch_and_filter(url):
        try:
            r = requests.get(url, timeout=Config.TIMEOUT, headers={"User-Agent": Config.USER_AGENT}, verify=False)
            if r.status_code == 200:
                text = TitanCore.traffic_compression_bridge(r)
                return TitanCore.process_logic(text)
        except Exception as e:
            TitanCore.log(f"Source Error: {url} -> {e}", "warn")
        return []

    @staticmethod
    def process_logic(text):
        extracted = []
        logo_regex = re.compile(r'tvg-logo="([^"]+)"', re.I)
        group_regex = re.compile(r'group-title="([^"]+)"', re.I)
        lines = text.splitlines()
        
        for i in range(len(lines)):
            if lines[i].startswith("#EXTINF"):
                info = lines[i]
                name = info.split(',')[-1].strip() or "Unknown Titan"
                
                if any(ex.lower() in info.lower() for ex in Config.EXCLUDED):
                    continue
                
                logo = logo_regex.search(info).group(1) if logo_regex.search(info) else ""
                group = group_regex.search(info).group(1) if group_regex.search(info) else "General"
                
                if i + 1 < len(lines):
                    url = lines[i+1].strip()
                    if url.startswith("http"):
                        url = TitanCore.bandwidth_optimizer(url)
                        is_hd = any(k.lower() in info.lower() or k in name.upper() for k in Config.HD_KEYWORDS)
                        extracted.append({
                            "name": name, "logo": logo, "url": url, 
                            "is_hd": is_hd, "group": group, "raw_info": info
                        })
        return extracted

# ==========================================
# FLASK CORE
# ==========================================
app = Flask(__name__)
Compress(app)
cache = {"channels": [], "last_updated": 0, "status": "INIT"}

def sync_engine():
    cache["status"] = "SYNCING"
    TitanCore.log("GLOBAL FUSION SYNC INITIATED...")
    all_ch = []
    with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
        futures = [executor.submit(TitanCore.fetch_and_filter, url) for url in Config.SOURCES]
        for f in as_completed(futures):
            all_ch.extend(f.result())
    
    seen = set()
    unique = []
    for c in all_ch:
        if c['url'] not in seen:
            unique.append(c)
            seen.add(c['url'])
    
    cache["channels"] = unique
    cache["last_updated"] = time.time()
    cache["status"] = "READY"
    TitanCore.log(f"FUSION COMPLETE: {len(unique)} CHANNELS.")

# ==========================================
# UI & ROUTES
# ==========================================
BASE_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Inter:wght@300;700&display=swap');
    :root { --p: #00f2fe; --bg: #020617; --glass: rgba(15, 23, 42, 0.9); }
    body { font-family: 'Inter', sans-serif; background: var(--bg); color: #f8fafc; margin: 0; text-align: center; }
    .header { padding: 50px 0; background: linear-gradient(180deg, rgba(0,242,254,0.1), transparent); }
    h1 { font-family: 'Orbitron'; background: linear-gradient(to right, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem; }
    .card { background: var(--glass); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 30px; margin: 20px auto; max-width: 800px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; padding: 20px; }
    .ch-card { background: rgba(30, 41, 59, 0.6); padding: 15px; border-radius: 12px; border: 1px solid rgba(0,242,254,0.2); }
    .btn { padding: 15px 30px; border-radius: 12px; text-decoration: none; font-weight: bold; background: #00f2fe; color: #000; display: inline-block; margin: 10px; }
    input { width: 80%; padding: 15px; border-radius: 10px; border: 1px solid #00f2fe; background: #000; color: #fff; margin-bottom: 20px; }
</style>
"""

@app.route('/')
def index():
    if not cache["channels"]: sync_engine()
    return render_template_string(BASE_STYLE + """
    <div class="header">
        <h1>{{ version }}</h1>
        <p>SYSTEM STATUS: <span style="color:#10b981;">{{ status }}</span></p>
    </div>
    <div class="container">
        <div class="card">
            <h3>🌍 NETWORK ACCESS</h3>
            <p>Local TV Link: <code>http://{{ ip }}:10000/playlist.m3u</code></p>
            <a href="/upload" class="btn">GET CLOUD LINK</a>
            <a href="/view/all" class="btn" style="background:#4facfe">BROWSE CHANNELS ({{ count }})</a>
        </div>
    </div>
    """, version=Config.VERSION, status=cache["status"], count=len(cache["channels"]), ip=TitanCore.get_local_ip())

@app.route('/upload')
def upload_playlist():
    m3u_content = "#EXTM3U\n"
    for ch in cache["channels"]:
        m3u_content += f"{ch['raw_info']}\n{ch['url']}\n"
    
    cloud_url = ExternalUploader.upload_to_web(m3u_content)
    if cloud_url:
        return f"<div style='background:#020617; color:#00f2fe; padding:50px; text-align:center; font-family:sans-serif;'><h2>CLOUD LINK READY:</h2><br><input value='{cloud_url}' style='width:80%; padding:10px;'><br><br><a href='/' style='color:#fff;'>Go Back</a></div>"
    return "Upload Failed. Use Local IP."

@app.route('/playlist.m3u')
def get_playlist():
    m3u = "#EXTM3U\n"
    for ch in cache["channels"]:
        m3u += f"{ch['raw_info']}\n{ch['url']}\n"
    return Response(m3u, mimetype='text/plain')

@app.route('/view/<mode>')
def view_mode(mode):
    if mode == "hd": filtered = [c for c in cache["channels"] if c["is_hd"]]
    elif mode == "sd": filtered = [c for c in cache["channels"] if not c["is_hd"]]
    else: filtered = cache["channels"]
    
    return render_template_string(BASE_STYLE + """
    <div class="container">
        <br><a href="/" class="btn">BACK</a>
        <div class="grid">
            {% for ch in filtered %}
            <div class="ch-card">
                <img src="{{ ch.logo }}" style="width:50px; height:50px; object-fit:contain;" onerror="this.src='https://cdn-icons-png.flaticon.com/512/5233/5233957.png'">
                <p style="font-size:12px; font-weight:bold;">{{ ch.name }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
    """, filtered=filtered)

def start_background():
    while True:
        time.sleep(Config.SYNC_INTERVAL)
        sync_engine()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=start_background, daemon=True).start()
    sync_engine()
    app.run(host='0.0.0.0', port=10000)
