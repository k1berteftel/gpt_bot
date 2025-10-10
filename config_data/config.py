from dataclasses import dataclass

from environs import Env

'''
    При необходимости конфиг базы данных или других сторонних сервисов
'''


@dataclass
class tg_bot:
    token: str
    admin_ids: list[int]
    channel_id: int


@dataclass
class DB:
    dns: str


@dataclass
class NatsConfig:
    servers: list[str]


@dataclass
class OpenAi:
    token: str


@dataclass
class Unifically:
    api_token: str


@dataclass
class VeoApi:
    api_key: str


@dataclass
class Proxy:
    login: str
    password: str
    ip: str
    port: int


@dataclass
class ImgBB:
    api_key: str


@dataclass
class Yookassa:
    account_id: str
    secret_key: str


@dataclass
class CryptoBot:
    token: str


@dataclass
class Subgram:
    api_key: str


@dataclass
class Config:
    bot: tg_bot
    db: DB
    nats: NatsConfig
    openai: OpenAi
    unifically: Unifically
    veo: VeoApi
    proxy: Proxy
    imgBB: ImgBB
    yookassa: Yookassa
    crypto_bot: CryptoBot
    subgram: Subgram


def load_config(path: str | None = None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(
        bot=tg_bot(
            token=env('token'),
            admin_ids=list(map(int, env.list('admins'))),
            channel_id=int(env('channel_id'))
        ),
        db=DB(
            dns=env('dns')
        ),
        nats=NatsConfig(
            servers=env.list('nats')
        ),
        openai=OpenAi(
            token=env('openai_token')
        ),
        unifically=Unifically(
            api_token=env('unifically_api_token')
        ),
        veo=VeoApi(
            api_key=env('veo_api_key')
        ),
        proxy=Proxy(
            login=env('login'),
            password=env('password'),
            ip=env('ip'),
            port=int(env('port'))
        ),
        imgBB=ImgBB(
            api_key=env('imgBB_api_key')
        ),
        yookassa=Yookassa(
            account_id=env('account_id'),
            secret_key=env('secret_key')
        ),
        crypto_bot=CryptoBot(
            token=env('cb_token')
        ),
        subgram=Subgram(
            api_key=env('subgram_api_key')
        )
    )
