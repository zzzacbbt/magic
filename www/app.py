import logging;
logging.basicConfig(level=logging.INFO)

import asyncio,os,json,time
from datetime import datetime

from aiohttp import web

routes = web.RouteTableDef()

@routes.get('/')
def index(request):
    return web.Response(body=b'<h1>Awesome</h1>')

async def init(loop):
    app = web.Application(loop=loop)
    app.add_routes(routes)
    srv = await loop.create_server(app.make_handler(),'172.23.0.3',11000)
    logging.info("server started at http://172.23.0.3:11000...")
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()


