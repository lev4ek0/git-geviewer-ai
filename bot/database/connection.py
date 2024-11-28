from datetime import datetime

from redis.client import Redis
from settings import SQLALCHEMY_ORM_CONFIG, redis_settings
from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncConnection,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

engine = create_async_engine(**SQLALCHEMY_ORM_CONFIG)


class PostgresConnection:
    def __init__(self):
        self.connection: AsyncConnection = engine
        self.engine = None

    async def connect(self):
        self.engine = create_async_engine(**SQLALCHEMY_ORM_CONFIG)
        async_session_maker = async_sessionmaker(bind=self.engine)
        self.connection = async_session_maker()
        return self.engine

    async def select(self, stmt):
        return await self.connection.execute(stmt)

    async def execute(self, *stmts):
        result = []
        try:
            for stmt in stmts:
                result.append(await self.connection.execute(stmt))
            await self.connection.commit()
        except Exception as e:
            await self.connection.rollback()
            raise e
        return result if len(stmts) > 1 else result[0]

    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


class RedisConnection:
    def __init__(self):
        self.connection = None

    def connect(self):
        redis = Redis(
            host=redis_settings.REDIS_HOST,
            port=redis_settings.REDIS_PORT,
            db=2,
            decode_responses=True,
        )
        self.connection = redis

    def set_expire(self, key, value, ttl=60):
        resp = self.connection.set(key, value)
        self.connection.expire(key, ttl)
        return resp

    def __setitem__(self, key, value):
        return self.connection.set(key, value)

    def __getitem__(self, item):
        return self.connection.get(item)


postgres_connection = PostgresConnection()
redis_connection = RedisConnection()


class Base(AsyncAttrs, DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.current_timestamp(),
    )

    def to_dict(self, excludes: list[str] = None):
        db_obj_dict = self.__dict__.copy()
        del db_obj_dict["_sa_instance_state"]
        for exclude in excludes or []:
            del db_obj_dict[exclude]
        return db_obj_dict

    def __str__(self) -> str:
        return f"{self.__class__.__name__} ({self.id})"
