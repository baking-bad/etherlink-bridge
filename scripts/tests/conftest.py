import pytest
from _pytest.fixtures import SubRequest
from gql import Client
from gql.client import SyncClientSession
from gql.transport.requests import RequestsHTTPTransport

from scripts.tests.dto import Bridge
from scripts.tests.dto import Native
from scripts.tests.dto import Token
from scripts.tests.dto import Wallet


def pytest_collection_modifyitems(items):
    function_order = {
        "test_indexer_is_healthy": 1,
        "test_l1_asset_whitelisted": 2,
        "test_l2_asset_whitelisted": 3,
        "test_asset_ticket_whitelisted": 4,
        "test_single_token_deposit": 5,
        "test_create_token_withdraw": 6,
        "test_finish_token_withdraw": 100,
    }
    function_mapping = {}
    for item in items:
        item_name = item.name.split('[', 1)[0]
        function_mapping[item] = function_order[item_name] if item_name in function_order else 50

    function_mapping = {k: v for k, v in sorted(function_mapping.items(), key=lambda x: x[1])}

    items[:] = [item for item in function_mapping]


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    if 'critical' in [mark.name for mark in item.own_markers]:
        result = outcome.get_result()

        if result.when == "call" and result.failed:
            print('FAILED')
            pytest.exit('Exiting pytest due to critical test failure', 1)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "critical: make test as critical"
    )


token_bridge_data_collection: dict[str, Token] = {
    'FA1.2': Token(
        l1_asset_id='KT1LpdETWYvPWCQTR2FEW6jE6dVqJqxYjdeW_0',
        l1_ticketer_address='KT1RvSp4yDKUABqWmv3pKGE9fA6iCGy7bqGh',
        l1_ticket_helper_address='KT1DHLWJorW9WB6ztkx1XcoaJKWXeTu9yoR1',
        l2_token_address='87dcbf128677ba36e79d47daf4eb4e51610e0150',
        ticket_hash=91175236955563041997969161541627053560043293816665252670757743059507881920725,
        ticket_content_hex='0707000005090a0000005f05020000005907040100000010636f6e74726163745f616464726573730a0000001c050a00000016018640' +
                           '607e2f2c3483ae9f15707d1823d4351742e0000704010000000a746f6b656e5f747970650a0000000b0501000000054641312e32'
    ),
    'FA2': Token(
        l1_asset_id='KT195Eb8T524v5VJ99ZzH2wpnPfQ2wJfMi6h_42',
        l1_ticketer_address='KT1VybveLaWhpQHKph28WcGwSy1ud22KSEan',
        l1_ticket_helper_address='KT1DNtHLr9T9zksZjZvQwgtx5XJwrW9wzETB',
        l2_token_address='cb5d40c6b1bdf5cd51b3801351b0a68d101a561b',
        ticket_hash=56913057262569210987124064945996187916231781764461777232724305614325812366043,
        ticket_content_hex='0707002a05090a0000007405020000006e07040100000010636f6e74726163745f616464726573730a0000001c050a00000016010562' +
                           '347c75e60f8ef9a15242d8accc705d8798a90007040100000008746f6b656e5f69640a0000000305002a0704010000000a746f6b656e' +
                           '5f747970650a00000009050100000003464132'
    ),
}

xtz_bridge_data: Native = Native(
    l1_asset_id='xtz',
    l1_ticketer_address='KT1Q6aNZ9aGro4DvBKwhKvVdia2UmVGsS9zE',
    l1_ticket_helper_address='KT1DWVsu4Jtu2ficZ1qtNheGPunm5YVniegT',
    l2_token_address='xtz',
    ticket_hash=10666650643273303508566200220257708314889526103361559239516955374962850039068,
    ticket_content_hex='...',
)


@pytest.fixture
def native_asset() -> Native:
    return xtz_bridge_data


@pytest.fixture
def fa1_2_token() -> Token:
    return token_bridge_data_collection['FA1.2']


@pytest.fixture
def fa2_token() -> Token:
    return token_bridge_data_collection['FA2']


@pytest.fixture(params=[token for token in token_bridge_data_collection.values()])
def token(request: SubRequest) -> Token:
    yield request.param


@pytest.fixture(params=[asset for asset in (token_bridge_data_collection | {'xtz': xtz_bridge_data}).values()])
def asset(request: SubRequest) -> Token | Native:
    yield request.param

@pytest.fixture
def ticket_router_tester_address() -> str:
    return 'KT1V8PLqiRQF7tLdc57a4mSdcsSfKaetjGC7'

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
        rollup_commitment_period=20,
        rollup_challenge_window=40,
        l1_time_between_blocks=8,
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
def indexer() -> SyncClientSession:
    transport = RequestsHTTPTransport(
        url='https://etherlink-bridge-indexer.dipdup.net/v1/graphql'
    )
    with Client(transport=transport) as session:
        yield session
