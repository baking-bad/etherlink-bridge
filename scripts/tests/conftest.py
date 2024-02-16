from typing import Any
from typing import AsyncGenerator

import pytest
from _pytest.fixtures import SubRequest
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from pydantic import BaseModel


class Bridge(BaseModel):
    l1_smart_rollup_address: str
    l1_rpc_url: str
    l2_rpc_url: str
    rollup_rpc_url: str
    l2_kernel_address: str
    l2_withdraw_precompile_address: str
    l2_native_withdraw_precompile_address: str


class Wallet(BaseModel):
    l1_private_key: str
    l1_public_key_hash: str
    l2_private_key: str
    l2_public_key: str
    l2_master_key: str


class Token(BaseModel):
    l1_asset_id: str
    l1_ticketer_address: str
    l1_ticket_helper_address: str
    l2_token_address: str
    ticket_hash: int


token_collection: dict[str, Token] = {
    'FA1.2': Token(
        l1_asset_id='KT1LpdETWYvPWCQTR2FEW6jE6dVqJqxYjdeW_0',
        l1_ticketer_address='KT1RvSp4yDKUABqWmv3pKGE9fA6iCGy7bqGh',
        l1_ticket_helper_address='KT1DHLWJorW9WB6ztkx1XcoaJKWXeTu9yoR1',
        l2_token_address='87dcbf128677ba36e79d47daf4eb4e51610e0150',
        ticket_hash=91175236955563041997969161541627053560043293816665252670757743059507881920725,
    ),
    'FA2': Token(
        l1_asset_id='KT195Eb8T524v5VJ99ZzH2wpnPfQ2wJfMi6h_42',
        l1_ticketer_address='KT1VybveLaWhpQHKph28WcGwSy1ud22KSEan',
        l1_ticket_helper_address='KT1DNtHLr9T9zksZjZvQwgtx5XJwrW9wzETB',
        l2_token_address='cb5d40c6b1bdf5cd51b3801351b0a68d101a561b',
        ticket_hash=56913057262569210987124064945996187916231781764461777232724305614325812366043,
    ),
}


@pytest.fixture
def fa1_2_token() -> Token:
    return token_collection['FA1.2']


@pytest.fixture
def fa2_token() -> Token:
    return token_collection['FA2']


@pytest.fixture(params=[token for name, token in token_collection.items()])
def token(request: SubRequest) -> Token:
    yield request.param


@pytest.fixture(scope='session', autouse=True)
def bridge() -> Bridge:
    return Bridge(
        l1_smart_rollup_address='sr1T4XVcVtBRzYy52edVTdgup9Kip4Wrmn97',
        l1_rpc_url='https://rpc.tzkt.io/oxfordnet',
        l2_rpc_url='https://etherlink.dipdup.net',
        rollup_rpc_url='https://etherlink-rollup-oxford.dipdup.net',
        l2_kernel_address='0x0000000000000000000000000000000000000000',
        l2_withdraw_precompile_address='0x0000000000000000000000000000000000000040',
        l2_native_withdraw_precompile_address='0x0000000000000000000000000000000000000020',
    )


@pytest.fixture(scope='session', autouse=True)
def wallet() -> Wallet:
    return Wallet(
        l1_private_key='edsk2nu78mRwg4V5Ka7XCJFVbVPPwhry8YPeEHRwzGQHEpGAffDvrH',
        l1_public_key_hash='tz1YG6P2GTQKFpd9jeuESam2vg6aA9HHRkKo',
        l2_private_key='8636c473b431be57109d4153735315a5cdf36b3841eb2cfa80b75b3dcd2d941a',
        l2_public_key='0xBefD2C6fFC36249ebEbd21d6DF6376ecF3BAc448',
        l2_master_key='9722f6cc9ff938e63f8ccb74c3daa6b45837e5c5e3835ac08c44c50ab5f39dc0',
    )


@pytest.fixture(scope='session', autouse=True)
async def indexer() -> AsyncGenerator[Client, Any]:
    transport = AIOHTTPTransport(
        url='https://etherlink-bridge-indexer.dipdup.net/v1/graphql'
    )
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        yield session
