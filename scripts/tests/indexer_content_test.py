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
                dipdup_index_aggregate { aggregate { sum { level } } }
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
        level_result_log = []
        for _ in range(3):
            response = indexer.execute(indexer_query, operation_name='IndexerStatus')
            level_result_log.append(int(response['dipdup_index_aggregate']['aggregate']['sum']['level']))
            assert response['dipdup_head_status'][0]['status'] == 'OK'
            sleep(bridge.l1_time_between_blocks)

        assert level_result_log == sorted(level_result_log)
        assert level_result_log[-1] > level_result_log[0]

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
        query_params = {'token_address': asset.l2_token_address}

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
        assert indexer_ticket_data['etherlink_tokens'][0]['id'] == asset.l2_token_address
