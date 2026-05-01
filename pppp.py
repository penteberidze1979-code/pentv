def start():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(core.findStableCore())

    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    start()
