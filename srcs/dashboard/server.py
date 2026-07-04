import json
import logging
import os
import asyncio
from aiohttp import web
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)

class DataEncoder(json.JSONEncoder):
	def default(self, o: Any) -> Any:
		if isinstance(o, deque):
			return (list(o))
		return (super().default(o))

async def handle_index(request: web.Request) -> web.FileResponse:
	current_dir: str = os.path.dirname(os.path.realpath(__file__))
	return (web.FileResponse(os.path.join(current_dir, 'index.html')))

async def handle_style(request: web.Request) -> web.FileResponse:
	current_dir: str = os.path.dirname(os.path.realpath(__file__))
	return (web.FileResponse(os.path.join(current_dir, 'style.css')))

async def handle_script(request: web.Request) -> web.FileResponse:
	current_dir: str = os.path.dirname(os.path.realpath(__file__))
	return (web.FileResponse(os.path.join(current_dir, 'script.js')))

async def handle_data(request: web.Request) -> web.Response:
	bot_data: dict = request.app['bot_data']
	return (web.json_response(bot_data, dumps=lambda obj: json.dumps(obj, cls=DataEncoder)))

async def dashboard(data: dict) -> None:
	app: web.Application = web.Application()
	app['bot_data'] = data
	app.router.add_get('/', handle_index)
	app.router.add_get('/style.css', handle_style)
	app.router.add_get('/script.js', handle_script)
	app.router.add_get('/api/data', handle_data)
	runner: web.AppRunner = web.AppRunner(app, access_log=None)
	await runner.setup()
	site: web.TCPSite = web.TCPSite(runner, 'localhost', 8080)
	logger.info("dashboard: http://localhost:8080")
	await site.start()
	try:
		while True:
			await asyncio.sleep(3600)
	except asyncio.CancelledError:
		logger.info("dashboard stopped")
		await runner.cleanup()
