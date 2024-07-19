from time import sleep

import pytest
from gql import gql
from gql.client import SyncClientSession
from graphql import DocumentNode

from scripts.tests.dto import Bridge
from scripts.tests.dto import Native
from scripts.tests.dto import Token


class TestIndexerContent:
    @pytest.fixture
    def indexer_query(self) -> DocumentNode:
        return gql(
            '''
            query IndexerStatus {
                dipdup_index(where: {type: {_neq: "tezos.operations"}}) {
                    name
                    level
                }
                dipdup_head_status { status }
            }
            
            query TezosToken($asset_id: String) {
                tezos_token_aggregate(where: {id: {_eq: $asset_id}}) {
                    aggregate { count }
                }
            }

            query EtherlinkToken($token_address: String) {
                etherlink_token_aggregate(where: {id: {_eq: $token_address}}) {
                    aggregate { count }
                }
            }
        
            query TokenTicket($ticket_hash: String) {
                tezos_ticket(where: {hash: {_eq: $ticket_hash}}) {
                    ticketer_address
                    token_id
                    etherlink_tokens { id }
                }
            }
            '''
        )

    @pytest.mark.critical
    def test_indexer_is_healthy(
        self,
        bridge: Bridge,
        indexer: SyncClientSession,
        indexer_query: gql,
    ):
        test_level_count = 3
        test_level_count = 1  # fixme: remove
        index_level: dict[str, list[int]] = {}
        count = 0
        while True:
            count += 1
            assert count <= bridge.l1_time_between_blocks * test_level_count
            response = indexer.execute(indexer_query, operation_name='IndexerStatus')
            assert response['dipdup_head_status'][0]['status'] == 'OK'
            collected_index_count = 0
            for index_data in response['dipdup_index']:
                index_name = index_data['name']
                if index_name not in index_level:
                    index_level[index_name] = []

                if len(index_level[index_name]) == test_level_count:
                    collected_index_count += 1
                    continue
                level = index_data['level']
                assert isinstance(level, int)
                if level not in index_level[index_name]:
                    index_level[index_name].append(level)
            if collected_index_count == len(response['dipdup_index']):
                break

            sleep(1)

        for level_list in index_level.values():
            assert len(level_list) == test_level_count
            assert level_list == sorted(level_list)

    def test_l1_asset_whitelisted(
        self,
        indexer: SyncClientSession,
        asset: Native | Token,
        indexer_query: gql,
    ):
        query_params = {'asset_id': asset.l1_asset_id}

        response = indexer.execute(indexer_query, variable_values=query_params, operation_name='TezosToken')
        assert response['tezos_token_aggregate']['aggregate']['count'] == 1

    def test_l2_asset_whitelisted(
        self,
        indexer: SyncClientSession,
        asset: Native | Token,
        indexer_query: gql,
    ):
        query_params = {'token_address': asset.l2_token_address.lower()}

        response = indexer.execute(indexer_query, variable_values=query_params, operation_name='EtherlinkToken')
        assert response['etherlink_token_aggregate']['aggregate']['count'] == 1

    def test_asset_ticket_whitelisted(
        self,
        indexer: SyncClientSession,
        asset: Native | Token,
        indexer_query: gql,
    ):
        query_params = {'ticket_hash': str(asset.ticket_hash)}

        response = indexer.execute(indexer_query, variable_values=query_params, operation_name='TokenTicket')
        assert len(response['tezos_ticket']) == 1
        indexer_ticket_data = response['tezos_ticket'][0]
        assert indexer_ticket_data['token_id'] == asset.l1_asset_id
        assert indexer_ticket_data['ticketer_address'] == asset.l1_ticketer_address
        assert indexer_ticket_data['etherlink_tokens'][0]['id'] == asset.l2_token_address.lower()
