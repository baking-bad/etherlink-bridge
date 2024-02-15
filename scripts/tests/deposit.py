import asyncio
from random import randint
from typing import Any
from typing import AsyncGenerator

import pytest
from gql import Client
from gql import gql
from gql.transport.aiohttp import AIOHTTPTransport
from graphql import DocumentNode
from pydantic import BaseModel

from scripts.tezos import deposit


class Bridge(BaseModel):
    rollup_address: str
    l1_rpc_url: str
    l2_rpc_url: str
    rollup_rpc_url: str


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


fa2_token = Token(
    l1_asset_id='KT195Eb8T524v5VJ99ZzH2wpnPfQ2wJfMi6h_42',
    l1_ticketer_address='KT1VybveLaWhpQHKph28WcGwSy1ud22KSEan',
    l1_ticket_helper_address='KT1DNtHLr9T9zksZjZvQwgtx5XJwrW9wzETB',
    l2_token_address='cb5d40c6b1bdf5cd51b3801351b0a68d101a561b',
    ticket_hash=56913057262569210987124064945996187916231781764461777232724305614325812366043,
)


@pytest.fixture
def bridge() -> Bridge:
    return Bridge(
        rollup_address='sr1T4XVcVtBRzYy52edVTdgup9Kip4Wrmn97',
        l1_rpc_url='https://rpc.tzkt.io/oxfordnet',
        l2_rpc_url='https://etherlink.dipdup.net',
        rollup_rpc_url='https://etherlink-rollup-oxford.dipdup.net',
    )


@pytest.fixture
def wallet() -> Wallet:
    return Wallet(
        l1_private_key='edsk2nu78mRwg4V5Ka7XCJFVbVPPwhry8YPeEHRwzGQHEpGAffDvrH',
        l1_public_key_hash='tz1YG6P2GTQKFpd9jeuESam2vg6aA9HHRkKo',
        l2_private_key='8636c473b431be57109d4153735315a5cdf36b3841eb2cfa80b75b3dcd2d941a',
        l2_public_key='0xBefD2C6fFC36249ebEbd21d6DF6376ecF3BAc448',
        l2_master_key='9722f6cc9ff938e63f8ccb74c3daa6b45837e5c5e3835ac08c44c50ab5f39dc0',
    )


@pytest.fixture
def token() -> Token:
    for token in [fa2_token]:
        yield token


@pytest.fixture
async def indexer() -> AsyncGenerator[Client, Any]:
    transport = AIOHTTPTransport(url="https://etherlink-bridge-indexer.dipdup.net/v1/graphql")
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        yield session


@pytest.fixture
def query() -> DocumentNode:
    return gql(
        """
query DepositQuery($l1_account: String, $operation_hash: String) {
  bridge_deposit(order_by: {created_at: desc}, where: {l1_transaction: {l1_account: {_eq: $l1_account}, operation_hash: {_eq: $operation_hash}}}) {
    l1_transaction {
      operation_hash
      l1_account
      l2_account
      ticket_hash
      amount
      ticket {
        token_id
      }
    }
    l2_transaction {
      l2_account
      ticket_hash
      amount
      l2_token {
        id
      }
    }
  }
}
"""
)


class TestDeposit:
    @pytest.mark.asyncio
    async def test_single_token_deposit(self, bridge: Bridge, wallet: Wallet, token: Token, indexer, query: DocumentNode, capfd):
        amount = randint(3, 20)

        deposit.callback(
            ticket_helper_address=token.l1_ticket_helper_address,
            amount=amount,
            receiver_address=wallet.l2_public_key,
            rollup_address=bridge.rollup_address,
            private_key=wallet.l1_private_key,
            rpc_url=bridge.l1_rpc_url,
        )
        captured = capfd.readouterr()
        operation_hash = captured.out[27:-1]

        params = {
            "l1_account": wallet.l1_public_key_hash,
            "operation_hash": operation_hash
        }
        async for session in indexer:
            result = {}
            for _ in range(20):
                result = await session.execute(query, variable_values=params)
                if len(result['bridge_deposit']) == 1:
                    break
                await asyncio.sleep(3)

            assert len(result['bridge_deposit']) == 1
            assert result['bridge_deposit'][0]['l1_transaction']['l1_account'] == wallet.l1_public_key_hash
            assert result['bridge_deposit'][0]['l1_transaction']['l2_account'] == wallet.l2_public_key[2:].lower()
            assert result['bridge_deposit'][0]['l2_transaction']['l2_account'] == wallet.l2_public_key[2:].lower()
            assert result['bridge_deposit'][0]['l1_transaction']['ticket_hash'] == str(token.ticket_hash)
            assert result['bridge_deposit'][0]['l2_transaction']['ticket_hash'] == str(token.ticket_hash)
            assert result['bridge_deposit'][0]['l1_transaction']['amount'] == str(amount)
            assert result['bridge_deposit'][0]['l2_transaction']['amount'] == str(amount)
            assert result['bridge_deposit'][0]['l1_transaction']['ticket']['token_id'] == token.l1_asset_id
            assert result['bridge_deposit'][0]['l2_transaction']['l2_token']['id'] == token.l2_token_address
