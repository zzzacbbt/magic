import orm
import asyncio
from models import User, Blog, Comment

async def test(loop):
    await orm.create_pool(loop=loop, user='www-data', password='www-data', database='awesome', db='mysql')

    u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')

    await  u.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))


for x in test():
    pass

