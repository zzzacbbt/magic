import asyncio
import logging
#logging.basicConfig(level=logging.INFO)
import aiomysql

def log(sql, args=()):
    logging.info('SQL: %s' % sql)

    
async def create_pool(loop, host='localhost', port=3306, 
    user='', password='', db='', charset='utf8mb4', autocommit=True,
    maxsize=10, minsize=1):
    logging.info("create database connection pool...")
    global pool
    pool = await aiomysql.create_pool(host=host, port=port, user=user, password=password, db=db, 
    charset=charset, autocommit=autocommit, maxsize=maxsize, minsize=minsize, loop=loop)
    
async def select(sql, args, size=None):
    log(sql,args)
    async with pool.acquire() as conn:
        #A cursor which returns results as a dictionary
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql.replace('?','%s'), args or ())
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await cur.fetchall()
            await cur.close()
        logging.info('row returned: %s' % len(rs))
        return rs

async def execute(sql, args, autocommit=True):
    log(sql)
    async with pool.acquire() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aipmysql.DictCursor) as cur:
                await cur.execute(sql.replace('?','%s'),args)
                affected = cur.rowcount
            if not autocommit:
                await conn.commit()
            await cur.close()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
        return affected
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)


class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default


    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)

class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, column_type='varchar(100)'):
        super().__init__(name, column_type, primary_key, default)


class IntergerField(Field):
    def __init__(self, name=None, primary_key=False, default=0, column_type='bigint'):
        super().__init__(name, column_type, primary_key, default)


class BooleanField(Field):
    def __init__(self, name=None, primary_key=False, default=None, column_type='boolean'):
        super().__init__(name, column_type, primary_key, default)


class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0, column_type='real'):
        super().__init__(name, column_type, primary_key, default)


class TextField(Field):
    def __init__(self, name=None, primary_key=False, default=None, column_type='text'):
        super().__init__(name, column_type, primary_key, default)
class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if __name__=="Model":
            return type.__new__(cls, name , bases, attrs)
        tableName = attrs.get('__table__', None) or name
        logging.info("Found model %s (table is %s)" %(name, tableName))
        mappings = dict()
        fields = []
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('Found mapping %s->%s' %(k, v))
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            #raise RuntimeError('Primary key no found')
            pass
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '%s' % f, fields))
        attrs['__mappings__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey
        attrs['__field__'] = fields
        attrs['__select__'] = "select %s, %s from %s" % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = "insert into %s (%s, %s) values (%s)" % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = "update %s set %s where %s=?" % (tableName, ', '.join(list(map(lambda f: '%s=?' % (mappings.get(f).name or f), fields))), primaryKey)
        attrs['__delete__'] = 'delete from %s where %s=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)
class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        super(Model,self).__init__(**kw)


    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attrubute '%s'" %key)
    

    def __setattr__(self, key, value):
        self[key] = value


    def getValue(self, key):
        return getattr(self, key, None)

    
    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value


    @classmethod
    async def findAll(cls, where=None, args=None, orderBy=None, limit=None):
        ' find objects by where clause. '
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)      
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]


    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        ' find number by select and where. '
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']


    @classmethod
    async def find(cls, pk):
        rs = await select("%s where '%s'=?" % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])
    

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)


    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)


    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to remove by primary key: affected rows: %s' % rows)







