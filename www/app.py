import logging;
logging.basicConfig(level=logging.INFO)

import asyncio,os,json,time

from aiohttp import web

routes = web.RouteTableDef()

@routes.get('/')
async def index(request):
    return web.Response(text="Awesome")


"""async def init(loop):
    app = web.Application(loop=loop)
    app.add_routes(routes)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()"""



app = web.Application()
app.add_routes(routes)
web.run_app(app,port=9000)
logging.info('server started at http://127.0.0.1:9000...')