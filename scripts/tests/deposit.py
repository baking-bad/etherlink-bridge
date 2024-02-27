import asyncio
from random import randint
from typing import Any
from typing import AsyncGenerator

import pytest
from gql import Client
from gql import gql
from graphql import DocumentNode
from pytezos import pytezos

from scripts.tezos import deposit
from scripts.tests.conftest import Bridge
from scripts.tests.conftest import Token
from scripts.tests.conftest import Wallet
from tezos.tests.helpers.contracts import TicketHelper


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
            indexed_operations = []
            for _ in range(20):
                response = await session.execute(bridge_deposit_query, variable_values=query_params)
                indexed_operations = response['bridge_deposit']
                if len(indexed_operations):
                    break
                await asyncio.sleep(3)

            assert indexed_operations == [{
                'l1_transaction': {
                    'operation_hash': operation_hash,
                    'l1_account': wallet.l1_public_key_hash,
                    'l2_account': wallet.l2_public_key[2:].lower(),
                    'ticket_hash': str(token.ticket_hash),
                    'amount': str(amount),
                    'ticket': {
                        'token_id': token.l1_asset_id
                    }
                },
                'l2_transaction': {
                    'l2_account': wallet.l2_public_key[2:].lower(),
                    'ticket_hash': str(token.ticket_hash),
                    'amount': str(amount),
                    'l2_token': {'id': token.l2_token_address}
                }
            }]


    @pytest.mark.asyncio
    async def test_batch_token_deposit(
        self,
        bridge: Bridge,
        wallet: Wallet,
        token: Token,
        indexer: AsyncGenerator[Client, Any],
        bridge_deposit_query: gql,
    ):
        batch_count = randint(3, 5)
        amount = randint(3, 20)

        manager = pytezos.using(shell=bridge.l1_rpc_url, key=wallet.l1_private_key)
        ticket_helper = TicketHelper.from_address(manager, token.l1_ticket_helper_address)
        token_helper = ticket_helper.get_ticketer().get_token()

        operations_group = (
            token_helper.disallow(manager, ticket_helper),
            token_helper.allow(manager, ticket_helper),
            ticket_helper.deposit(
                rollup=bridge.l1_smart_rollup_address,
                receiver=bytes.fromhex(wallet.l2_public_key.replace('0x', '')),
                amount=amount,
            ),
        )*batch_count

        opg = manager.bulk(* operations_group).send()
        manager.wait(opg)
        operation_hash = opg.hash()

        assert operation_hash[0] == 'o'
        assert len(operation_hash) == 51

        query_params = {'operation_hash': operation_hash}

        async for session in indexer:
            indexed_operations = []
            for _ in range(20):
                response = await session.execute(bridge_deposit_query, variable_values=query_params)
                indexed_operations = response['bridge_deposit']
                if len(indexed_operations):
                    break
                await asyncio.sleep(3)

            assert len(indexed_operations) == batch_count
            for _ in range(batch_count):
                assert indexed_operations[_] == {
                    'l1_transaction': {
                        'operation_hash': operation_hash,
                        'l1_account': wallet.l1_public_key_hash,
                        'l2_account': wallet.l2_public_key[2:].lower(),
                        'ticket_hash': str(token.ticket_hash),
                        'amount': str(amount),
                        'ticket': {
                            'token_id': token.l1_asset_id
                        }
                    },
                    'l2_transaction': {
                        'l2_account': wallet.l2_public_key[2:].lower(),
                        'ticket_hash': str(token.ticket_hash),
                        'amount': str(amount),
                        'l2_token': {'id': token.l2_token_address}
                    }
                }

            # Check matched operations order
