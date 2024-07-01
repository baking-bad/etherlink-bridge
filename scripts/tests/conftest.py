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
    'tzBTC': Token(
        l1_asset_id='KT1V7YkCUvuLCcMvrNfxvfP7AYdh7SUy3gVk_0',
        l1_ticketer_address='KT1KnYz9eRVQHYgj25FMdQ9fo5f9SUEonzxe',
        l1_ticket_helper_address='KT1WmUoTU91RVjGv8MHW5DFRn8daoFvnoNBh',
        l2_token_address='54b20569c0aa92a5618589142b2d5cc5fe6fe426',
        ticket_hash=38501601458255431664549467905666194270780968624079854711059999119424038560263,
        ticket_content_hex='...'
    ),
    'SIRS': Token(
        l1_asset_id='KT1Dhb74UkncT5FcZfqmgnnXsBe3LBVXbpRb_0',
        l1_ticketer_address='KT1BSE3Vzu2aMMg1Aa35vnM1MMPq4YAJRU5G',
        l1_ticket_helper_address='KT1KvgaQ9Eztr3hXzV2tGT85fPRPGmXBzF7r',
        l2_token_address='1b674b7d28d3da4bb0cbda959de2bcebe2ac83e8',
        ticket_hash=106896103357068750276116957911853427818210703182371619532851114745162512601884,
        ticket_content_hex='...'
    ),
    'USDt': Token(
        l1_asset_id='KT1TJK6aTreCyfrrEjj1ZRPUmKdnLXfcgAAa_0',
        l1_ticketer_address='KT1LBv2tVJt17UXC32SS6Vtbtg7yPcJ8scbb',
        l1_ticket_helper_address='KT1H4TBKdAjCxQKBcdPqnfLvLbhShZ2CPC51',
        l2_token_address='e4bf1873cfdaed33bab4e0f5788cba6d03a267f0',
        ticket_hash=39756979904490530639324653565564362862566450403546985891700568436159160316336,
        ticket_content_hex='...'
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
        l1_private_key='edskRqDjCTNPh8QttChynaNcMwNqLKuEdtcrvSqmJojzDUFtBqtvbaXgs5eWpyQ2AABxS8FSZjzKytrLs38E4M9GcpAdiQjnUY',
        l1_public_key_hash='tz1cdDUja6hsp4vNUBNmjVpEBDSYhDVLxg2X',
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
