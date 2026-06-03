# Flat CLI / notebook default constants, sourced from the active network config
# (networks/{NETWORK}.toml). Interim shape — the target is consumers importing
# the config object directly; see memory/cli-config-object-refactor.md.
from eth_utils import to_checksum_address  # type: ignore[attr-defined]

from scripts.networks import load_network

_network = load_network()
_token = _network.default_token_config()

# Network / accounts:
SMART_ROLLUP_ADDRESS = _network.network.smart_rollup_address
XTZ_TICKET_HELPER = _network.native.l1_ticket_helper_address
TEZOS_PRIVATE_KEY = _network.accounts.l1_private_key
TEZOS_RPC_URL = _network.network.l1_rpc_url
ETHERLINK_RPC_URL = _network.network.l2_rpc_url
ETHERLINK_PRIVATE_KEY = _network.accounts.l2_private_key
KERNEL_ADDRESS = _network.network.l2_kernel_address
FA_WITHDRAWAL_PRECOMPILE = _network.network.l2_withdraw_precompile_address
XTZ_WITHDRAWAL_PRECOMPILE = _network.network.l2_native_withdraw_precompile_address
ETHERLINK_ROLLUP_NODE_URL = _network.network.rollup_rpc_url

# Testing scenarios:
PRINT_DEBUG_LOG = False

# Default token + bridge setup:
TEZOS_TOKEN_ADDRESS = _token.l1_token_address
TEZOS_TOKEN_TYPE = _token.token_type
TICKETER_ADDRESS = _token.l1_ticketer_address
ERC20_PROXY_ADDRESS = to_checksum_address('0x' + _token.l2_token_address)
TOKEN_BRIDGE_HELPER_ADDRESS = _token.l1_ticket_helper_address
TICKET_ROUTER_TESTER_ADDRESS = _network.network.ticket_router_tester_address
XTZ_TICKETER_ADDRESS = _network.native.l1_ticketer_address
FAST_WITHDRAWAL_CONTRACT = _network.network.fast_withdrawal_contract
INDEXER_GRAPHQL_URL = _network.network.indexer_graphql_url
BLOCKSCOUT_EXPLORER_URL = _network.network.blockscout_explorer_url
TZKT_EXPLORER_URL = _network.network.tzkt_explorer_url
