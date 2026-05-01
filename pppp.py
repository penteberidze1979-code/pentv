import os
import time
import requests
import logging
from flask import Flask, Response, jsonify
from flask_compress import Compress
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# ==========================================
# TITAN OMEGA X-1 - IPTV CORE CONFIGURATION
# ==========================================

app = Flask(__name__)
Compress(app)  # ოპტიმიზაცია: მონაცემთა შეკუმშვა სწრაფი გადაცემისთვის

# ლოგირების სისტემა
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [TITAN_LOG] - %(message)s')

# მრავალდონიანი წყაროების სისტემა (Redundancy)
SOURCES = [
    "https://iptv-org.github.io/iptv/index.m3u",
    "https://iptv-org.github.io/iptv/index.nsfw.m3u" # ალტერნატიული წყარო
]

# კონფიგურაცია
CONFIG = {
    "CACHE_TIMEOUT": 14400,  # 4 საათი
    "REQUEST_TIMEOUT": 45,   # გაზრდილი თაიმაუტი დიდი სიებისთვის
    "MAX_WORKERS": 5,        # პარალელური დამუშავება
    "VERSION": "TITAN OMEGA GLOBAL V50.1-PRO",
    "EXCLUDED_KEYWORDS": ["Adult", "XXX", "18+"] # ფილტრაციის მექანიზმი
}

# ინტელექტუალური ქეშირების სისტემა
cache = {
    "data": None,
    "last_updated": 0,
    "status": "INITIALIZING",
    "total_channels": 0
}

def filter_content(line):
    """კონტენტის დინამიური ფილტრაცია"""
    for keyword in CONFIG["EXCLUDED_KEYWORDS"]:
        if keyword.lower() in line.lower():
            return False
    return True

def fetch_source(url):
    """ინდივიდუალური წყაროს სინქრონიზაცია"""
    try:
        logging.info(f"სინქრონიზაცია წყაროსთან: {url}")
        response = requests.get(url, timeout=CONFIG["REQUEST_TIMEOUT"])
        if response.status_code == 200:
            return response.text
    except Exception as e:
        logging.error(f"შეცდომა წყაროსთან {url}: {e}")
    return None

def build_global_playlist():
    """გლობალური სიის გენერაცია და ოპტიმიზაცია"""
    logging.info("TITAN OMEGA: გლობალური რეკონსტრუქცია დაწყებულია...")
    
    combined_lines = ["#EXTM3U x-tvg-url=\"http://itv.com/epg/epg.xml.gz\""]
    
    with ThreadPoolExecutor(max_workers=CONFIG["MAX_WORKERS"]) as executor:
        results = list(executor.map(fetch_source, SOURCES))
    
    for result in results:
        if result:
            lines = result.splitlines()
            for i in range(len(lines)):
                line = lines[i]
                if line.startswith("#EXTM3U"):
                    continue
                
                # თუ ხაზი არის არხის აღწერა (#EXTINF)
                if line.startswith("#EXTINF"):
                    # ვამოწმებთ შემდეგ ხაზს (URL-ს) და თავად აღწერას
                    if i + 1 < len(lines) and filter_content(line):
                        combined_lines.append(line)
                        combined_lines.append(lines[i+1])
    
    cache["total_channels"] = len(combined_lines) // 2
    logging.info(f"რეკონსტრუქცია დასრულებულია. სულ: {cache['total_channels']} არხი.")
    return "\n".join(combined_lines)

@app.route('/')
def index():
    """TITAN OMEGA UI - სტატუსის პანელი"""
    return jsonify({
        "system": "TITAN OMEGA X-1",
        "status": "OPERATIONAL",
        "endpoints": {
            "/playlist.m3u": "მთავარი IPTV სია",
            "/status": "სისტემური დიაგნოსტიკა",
            "/refresh": "იძულებითი განახლება"
        }
    })

@app.route('/status')
def status():
    """დეტალური დიაგნოსტიკური მონაცემები"""
    return jsonify({
        "project": CONFIG["VERSION"],
        "uptime_status": "ACTIVE",
        "cache_age_seconds": time.time() - cache["last_updated"],
        "total_channels_indexed": cache["total_channels"],
        "next_update_in": CONFIG["CACHE_TIMEOUT"] - (time.time() - cache["last_updated"]),
        "memory_optimization": "ENABLED",
        "compression": "GZIP_ACTIVE"
    })

@app.route('/playlist.m3u')
def get_playlist():
    """სიის მიწოდება ჭკვიანი ქეშირების გამოყენებით"""
    current_time = time.time()
    
    # ქეშის ვალიდაცია
    if cache["data"] is None or (current_time - cache["last_updated"]) > CONFIG["CACHE_TIMEOUT"]:
        cache["data"] = build_global_playlist()
        cache["last_updated"] = current_time
        cache["status"] = "UPDATED"
    
    return Response(
        cache["data"], 
        mimetype='application/x-mpegurl',
        headers={
            "Content-Disposition": "attachment; filename=titan_omega.m3u",
            "Cache-Control": f"max-age={CONFIG['CACHE_TIMEOUT']}"
        }
    )

@app.route('/refresh')
def force_refresh():
    """იძულებითი სინქრონიზაციის ჰუკი"""
    cache["data"] = build_global_playlist()
    cache["last_updated"] = time.time()
    return jsonify({"message": "TITAN OMEGA: Cache purged and reloaded successfully."})

if __name__ == '__main__':
    # პორტის დინამიური ადაპტაცია
    port = int(os.environ.get("PORT", 10000))
    logging.info(f"TITAN OMEGA X-1 გაშვებულია პორტზე: {port}")
    
    # Threaded=True უზრუნველყოფს მრავალჯერად კავშირს
    app.run(host='0.0.0.0', port=port, threaded=True)
