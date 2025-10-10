import datetime

from sqlalchemy import BigInteger, VARCHAR, ForeignKey, DateTime, Boolean, Column, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


class UsersTable(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(VARCHAR)
    name: Mapped[str] = mapped_column(VARCHAR)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    balance: Mapped[int] = mapped_column(Integer, default=20)
    referral: Mapped[int] = mapped_column(BigInteger, default=None, nullable=True)
    join: Mapped[str] = mapped_column(VARCHAR, default=None, nullable=True)
    refs: Mapped[int] = mapped_column(Integer, default=0)
    gens: Mapped[int] = mapped_column(Integer, default=0)
    earn: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[int] = mapped_column(Integer, default=1)
    activity: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), default=func.now())
    entry: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), default=func.now())
    last_generate: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), default=None, nullable=True)


class DeeplinksTable(Base):
    __tablename__ = 'deeplinks'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    link: Mapped[str] = mapped_column(VARCHAR)
    entry: Mapped[int] = mapped_column(BigInteger, default=0)
    income: Mapped[int] = mapped_column(Integer, default=0)
    earned: Mapped[int] = mapped_column(Integer, default=0)
    today: Mapped[int] = mapped_column(Integer, default=0)
    week: Mapped[int] = mapped_column(Integer, default=0)
    create: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), default=func.now())


class RatesTable(Base):
    __tablename__ = 'rates'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    amount: Mapped[int] = mapped_column(Integer, nullable=False)


class AdminsTable(Base):
    __tablename__ = 'admins'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(VARCHAR)


class OneTimeLinksIdsTable(Base):
    __tablename__ = 'links'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    link: Mapped[str] = mapped_column(VARCHAR)


class OpTable(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    chat_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(VARCHAR)
    link: Mapped[str] = mapped_column(VARCHAR)
    entry: Mapped[int] = mapped_column(Integer, default=0)


class StaticTable(Base):
    __tablename__ = 'static'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    total: Mapped[int] = mapped_column(Integer, default=0)
    today: Mapped[int] = mapped_column(Integer, default=0)
    week: Mapped[int] = mapped_column(Integer, default=0)
    month: Mapped[int] = mapped_column(Integer, default=0)


