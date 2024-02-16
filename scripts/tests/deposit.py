import asyncio
from random import randint
from typing import Any
from typing import AsyncGenerator

import pytest
from gql import Client
from gql import gql
from graphql import DocumentNode

from scripts.tezos import deposit
from scripts.tests.conftest import Bridge
from scripts.tests.conftest import Token
from scripts.tests.conftest import Wallet


class TestDeposit:
    @pytest.fixture
    def bridge_deposit_query(self) -> DocumentNode:
        return gql(
            '''
            query BridgeDepositQuery($operation_hash: String) {
                bridge_deposit(
                    order_by: {created_at: desc},
                    where: {
                        l1_transaction: {
                            operation_hash: {_eq: $operation_hash}
                        }
                    }
                ) {
                    l1_transaction {
                        operation_hash, l1_account, l2_account, ticket_hash, amount, ticket {token_id}
                    }
                    l2_transaction {
                        l2_account, ticket_hash, amount, l2_token {id}
                    }
                }
            }
            '''
        )

    @pytest.mark.asyncio
    async def test_single_token_deposit(
        self,
        bridge: Bridge,
        wallet: Wallet,
        token: Token,
        indexer: AsyncGenerator[Client, Any],
        bridge_deposit_query: gql,
    ):
        amount = randint(3, 20)

        operation_hash = deposit.callback(
            ticket_helper_address=token.l1_ticket_helper_address,
            amount=amount,
            receiver_address=wallet.l2_public_key,
            rollup_address=bridge.l1_smart_rollup_address,
            private_key=wallet.l1_private_key,
            rpc_url=bridge.l1_rpc_url,
        )

        assert operation_hash[0] == 'o'
        assert len(operation_hash) == 51

        query_params = {'operation_hash': operation_hash}

        async for session in indexer:
            for _ in range(20):
                result = await session.execute(bridge_deposit_query, variable_values=query_params)
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
