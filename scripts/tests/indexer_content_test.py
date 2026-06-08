import pytest
from gql import gql
from gql.client import SyncClientSession
from graphql import DocumentNode

from scripts.helpers.utility import get_etherlink_web3
from scripts.tests.dto import Bridge
from scripts.tests.dto import Native
from scripts.tests.dto import Token

pytestmark = pytest.mark.integration

# An index may sit a little behind the chain head and still be healthy; only a
# large gap means the indexer can't keep up and fresh ops won't be indexed.
# Tune up if it false-positives on a healthy-but-busy indexer.
INDEXER_MAX_LAG_BLOCKS = 1000


class TestIndexerContent:
    @pytest.fixture
    def indexer_query(self) -> DocumentNode:
        return gql(
            '''
            query IndexerStatus {
                dipdup_head(where: {name: {_eq: "tzkt"}}) {
                    level
                }
                dipdup_index {
                    name
                    level
                    status
                    type
                }
            }
            
            query TezosToken($asset_id: String) {
                tezos_token_aggregate(where: {id: {_eq: $asset_id}}) {
                    aggregate { count }
                }
            }

            query TokenMetadata($asset_id: String) {
                tezos_token(where: {id: {_eq: $asset_id}}) {
                    symbol
                    name
                    decimals
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
                    etherlink_token { id }
                }
            }
            '''
        )

    @pytest.mark.critical
    def test_indexer_is_healthy(
        self,
        bridge: Bridge,
        indexer: SyncClientSession,
        indexer_query: DocumentNode,
    ) -> None:
        # An index reports the block level it has processed; compare it to the
        # chain head (L1 for `tezos.*` indexes, L2 for `etherlink_*`). A `status`
        # check alone is not enough — DipDup keeps EVM indexes at `syncing` even
        # when they are caught up, so the real health signal is the gap to head.
        l2_head = get_etherlink_web3(bridge.l2_rpc_url).eth.block_number

        response = indexer.execute(indexer_query, operation_name='IndexerStatus')
        l1_head = response['dipdup_head'][0]['level']

        for index in response['dipdup_index']:
            name, status = index['name'], index['status']
            assert status not in ('failed', 'disabled'), f"Index '{name}': {status}"

            head = l1_head if index['type'].startswith('tezos') else l2_head
            lag = head - index['level']
            assert lag < INDEXER_MAX_LAG_BLOCKS, (
                f"Index '{name}' is {lag} blocks behind the chain head "
                f"(limit {INDEXER_MAX_LAG_BLOCKS}). Either the indexer is genuinely "
                f"lagging — no point testing fresh operations against it — or the "
                f"limit is too tight: raise INDEXER_MAX_LAG_BLOCKS if this is a false "
                f"positive."
            )

    def test_l1_asset_whitelisted(
        self,
        indexer: SyncClientSession,
        asset: Native | Token,
        indexer_query: DocumentNode,
    ) -> None:
        query_params = {'asset_id': asset.l1_asset_id}

        response = indexer.execute(
            indexer_query, variable_values=query_params, operation_name='TezosToken'
        )
        assert response['tezos_token_aggregate']['aggregate']['count'] == 1

    def test_l2_asset_whitelisted(
        self,
        indexer: SyncClientSession,
        asset: Native | Token,
        indexer_query: DocumentNode,
    ) -> None:
        query_params = {'token_address': asset.l2_token_address.lower()}

        response = indexer.execute(
            indexer_query, variable_values=query_params, operation_name='EtherlinkToken'
        )
        assert response['etherlink_token_aggregate']['aggregate']['count'] == 1

    def test_asset_has_metadata(
        self,
        indexer: SyncClientSession,
        asset: Native | Token,
        indexer_query: DocumentNode,
    ) -> None:
        query_params = {'asset_id': asset.l1_asset_id}

        response = indexer.execute(
            indexer_query, variable_values=query_params, operation_name='TokenMetadata'
        )
        tokens = response['tezos_token']
        assert len(tokens) == 1
        # Symbol/name come from the metadata service at registration; missing them
        # means a metadata-datasource misconfig (e.g. wrong network for the L1).
        assert tokens[0]['symbol']
        assert tokens[0]['name']
        assert tokens[0]['decimals'] is not None

    def test_asset_ticket_whitelisted(
        self,
        indexer: SyncClientSession,
        asset: Native | Token,
        indexer_query: DocumentNode,
    ) -> None:
        query_params = {'ticket_hash': str(asset.ticket_hash)}

        response = indexer.execute(
            indexer_query, variable_values=query_params, operation_name='TokenTicket'
        )
        assert len(response['tezos_ticket']) == 1
        indexer_ticket_data = response['tezos_ticket'][0]
        assert indexer_ticket_data['token_id'] == asset.l1_asset_id
        assert indexer_ticket_data['ticketer_address'] == asset.l1_ticketer_address
        assert (
            indexer_ticket_data['etherlink_token']['id']
            == asset.l2_token_address.lower()
        )
