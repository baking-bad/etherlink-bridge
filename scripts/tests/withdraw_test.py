from random import randint
from time import sleep

import pytest
from eth_utils import to_checksum_address
from gql import gql
from gql.client import SyncClientSession
from graphql import DocumentNode
from pytezos import pytezos

from scripts.etherlink import withdraw
from scripts.helpers.utility import make_address_bytes
from scripts.tests.dto import Bridge
from scripts.tests.dto import Token
from scripts.tests.dto import Wallet


class TestWithdraw:
    @pytest.fixture
    def bridge_withdrawal_query(self) -> DocumentNode:
        return gql(
            """
            query BridgeWithdrawal($transaction_hash: String) {
                bridge_withdrawal(where: {l2_transaction: {transaction_hash: {_eq: $transaction_hash}}}) {
                    l2_transaction {
                        transaction_hash
                        l1_account
                        l2_account
                        ticket_hash
                        l2_token {
                            id
                            ticket {
                                ticketer_address
                            }
                        }
                    }
                    l1_transaction_id
                    outbox_message {
                        commitment_id
                        proof
                    }
                }
            }
        """
        )

    @pytest.fixture
    def bridge_pending_withdrawal_query(self) -> DocumentNode:
        return gql(
            """
            query FindPendingWithdrawalOperation($l2_account: String, $ticket_hash: String) {
                bridge_withdrawal(
                    where: {
                        l1_transaction_id: {_is_null: true}
                        l2_transaction: {
                            l2_account: {_eq: $l2_account}
                            ticket_hash: {_eq: $ticket_hash},
                        }
                    },
                    order_by: {l2_transaction: {level: desc}},
                    limit: 1
                )
                {
                    l2_transaction_id
                }
            }

            query FetchOutboxMessageProof($l2_transaction_id: uuid) {
                bridge_withdrawal(where: {l2_transaction_id: {_eq: $l2_transaction_id}}) {
                    outbox_message {
                        commitment {
                            inbox_level
                            hash
                        }
                        level
                        index
                        proof
                    }
                }
            }
        """
        )

    def test_create_token_withdraw(
        self,
        bridge: Bridge,
        wallet: Wallet,
        token: Token,
        indexer: SyncClientSession,
        bridge_withdrawal_query: gql,
        bridge_pending_withdrawal_query: gql,
    ):
        amount = randint(3, 10)

        transaction_hash = withdraw.callback(
            erc20_proxy_address=to_checksum_address(token.l2_token_address.lower()),
            tezos_side_router_address=token.l1_ticketer_address,
            amount=amount,
            ticketer_address_bytes=make_address_bytes(token.l1_ticketer_address),
            ticket_content_bytes=token.ticket_content_hex,
            receiver_address=wallet.l1_public_key_hash,
            withdraw_precompile=bridge.l2_withdraw_precompile_address,
            etherlink_private_key=wallet.l2_private_key,
            etherlink_rpc_url=bridge.l2_rpc_url,
        )

        transaction_hash = transaction_hash.removeprefix('0x')
        assert transaction_hash

        query_params = {'transaction_hash': transaction_hash}
        indexed_operations = []
        for _ in range(20):
            response = indexer.execute(bridge_withdrawal_query, variable_values=query_params)
            indexed_operations = response['bridge_withdrawal']
            if len(indexed_operations) and indexed_operations[0]['outbox_message'] is not None:
                break
            sleep(3)

        assert indexed_operations == [
            {
                'l2_transaction': {
                    'transaction_hash': transaction_hash,
                    'l1_account': wallet.l1_public_key_hash,
                    'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
                    'ticket_hash': str(token.ticket_hash),
                    'l2_token': {
                        'id': token.l2_token_address.lower(),
                        'ticket': {
                            'ticketer_address': token.l1_ticketer_address,
                        }
                    },
                },
                'outbox_message': {
                    'commitment_id': None,
                    'proof': None,
                },
                'l1_transaction_id': None,
            },
        ]

    def test_finish_token_withdraw(
        self,
        bridge: Bridge,
        wallet: Wallet,
        token: Token,
        indexer: SyncClientSession,
        bridge_pending_withdrawal_query: gql,
    ):
        query_params = {
            'l2_account': wallet.l2_public_key.removeprefix('0x').lower(),
            'ticket_hash': str(token.ticket_hash),
        }
        response = indexer.execute(
            bridge_pending_withdrawal_query,
            variable_values=query_params,
            operation_name='FindPendingWithdrawalOperation'
        )
        assert len(response['bridge_withdrawal']) == 1
        l2_operation_id = response['bridge_withdrawal'][0]['l2_transaction_id']
        assert l2_operation_id

        query_params = {'l2_transaction_id': l2_operation_id}
        for _ in range(bridge.rollup_challenge_window+bridge.rollup_commitment_period*2):
            response = indexer.execute(
                bridge_pending_withdrawal_query,
                variable_values=query_params,
                operation_name='FetchOutboxMessageProof'
            )
            cemented_withdrawal = response['bridge_withdrawal'][0]
            if cemented_withdrawal['outbox_message']['proof'] and cemented_withdrawal['outbox_message']['commitment']:
                break

            sleep(bridge.l1_time_between_blocks)

        assert cemented_withdrawal

        manager = pytezos.using(shell=bridge.l1_rpc_url, key=wallet.l1_private_key)
        opg = manager.smart_rollup_execute_outbox_message(
            bridge.l1_smart_rollup_address,
            cemented_withdrawal['outbox_message']['commitment']['hash'],
            bytes.fromhex(cemented_withdrawal['outbox_message']['proof']),
        ).send()
        manager.wait(opg)

        operation_hash = opg.hash()
        assert operation_hash

        # todo: compare operations
