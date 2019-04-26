import orm
import asyncio
from models import User, Blog, Comment

loop = asyncio.get_event_loop()


async def test(loop):
    pool = await orm.create_pool(loop=loop, user='www-data', password='www-data', db='awesome')
    u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')

    await  u.save()

    



loop.run_until_complete(test(loop))
pool.close()
loop.close()



