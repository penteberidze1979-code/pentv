from flask import Flask
import asyncio
import os

app = Flask(__name__)

# აქ ავტომატურად დაემატება სტატუსის გვერდი შესამოწმებლად
@app.route('/status')
def status():
    return {"status": "ACTIVE", "message": "IPTV Server is running"}

@app.route('/playlist.m3u')
def playlist():
    # აქ მომავალში ჩავწერთ არხების გამოტანის ლოგიკას
    return "#EXTM3U\n#EXTINF:-1,Test Channel\nhttp://example.com/stream"

def start():
    # პორტის გამართვა Render-ისთვის
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    start()
