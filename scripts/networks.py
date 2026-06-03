"""Loader for per-network bridge configs (``networks/{l1}-{l2}.toml``).

A single source of network parameters, test accounts and the whitelisted token
set, selected by the ``NETWORK`` env var. Pure file IO — safe to call at import
/ pytest-collection time (no chain access here; ticket data is derived at
fixture-build time, see ``scripts/tests/conftest.py``).
"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_NETWORK = 'shadownet-etherlink'
NETWORKS_DIR = Path(__file__).resolve().parent.parent / 'networks'


@dataclass
class NetworkParams:
    l1_rpc_url: str
    l2_rpc_url: str
    rollup_rpc_url: str
    indexer_graphql_url: str
    smart_rollup_address: str
    fast_withdrawal_contract: str
    ticket_router_tester_address: str
    l2_kernel_address: str
    l2_withdraw_precompile_address: str
    l2_native_withdraw_precompile_address: str
    tzkt_explorer_url: str
    blockscout_explorer_url: str


@dataclass
class Accounts:
    l1_private_key: str
    l1_public_key_hash: str
    l2_private_key: str
    l2_public_key: str
    l2_master_key: str


@dataclass
class TokenConfig:
    symbol: str
    token_type: str
    l1_token_address: str
    l1_ticketer_address: str
    l1_ticket_helper_address: str
    l2_token_address: str

    def __post_init__(self) -> None:
        # Accept the L2 address in any form (checksummed / 0x / lowercase) and
        # canonicalise to lowercase-without-0x, matching the indexer's token id.
        self.l2_token_address = self.l2_token_address.lower().removeprefix('0x')


@dataclass
class NativeConfig:
    l1_ticketer_address: str
    l1_ticket_helper_address: str


@dataclass
class NetworkConfig:
    name: str
    default_token: str
    network: NetworkParams
    accounts: Accounts
    native: NativeConfig
    tokens: list[TokenConfig]

    def default_token_config(self) -> TokenConfig:
        return next(t for t in self.tokens if t.symbol == self.default_token)


def load_network(name: str | None = None) -> NetworkConfig:
    """Loads the config for the given network (default: ``$NETWORK`` or
    ``shadownet-etherlink``) from ``networks/{name}.toml``."""

    name = name or os.environ.get('NETWORK', DEFAULT_NETWORK)
    path = NETWORKS_DIR / f'{name}.toml'
    with path.open('rb') as f:
        data = tomllib.load(f)

    return NetworkConfig(
        name=data['name'],
        default_token=data['default_token'],
        network=NetworkParams(**data['network']),
        accounts=Accounts(**data['accounts']),
        native=NativeConfig(**data['native']),
        tokens=[TokenConfig(**token) for token in data['tokens']],
    )
