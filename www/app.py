import logging;
logging.basicConfig(level=logging.INFO)

import asyncio,os,json,time

from aiohttp import web
from coroweb import add_routes,add_static
import orm

from models import User
routes = web.RouteTableDef()





async def init(loop):
    await orm.create_pool(host='127.0.0.1', port=3306, user='www-data',password='www-data', db='awesome',loop=loop)
    app = web.Application(loop=loop)
    add_routes(app,'handles')
    add_static(app)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()



"""app = web.Application()
app.add_routes(routes)
web.run_app(app,port=9000)
logging.info('server started at http://127.0.0.1:9000...')"""