"""The single `bridge` CLI entry point.

All subcommands are registered flat under one group. Per-network option defaults
(RPC URLs, test keys, contract addresses) are injected at the group level via
``Context.default_map`` from the active network config (selected by ``NETWORK=``),
so commands carry no baked-in defaults and the same CLI works on any network.
"""

from typing import Any

import click

from scripts.networks import NetworkConfig, load_network

from scripts.tezos.fa_deposit import fa_deposit_command
from scripts.tezos.get_ticketer_params import get_ticketer_params_command
from scripts.tezos.deploy_ticketer import deploy_ticketer_command
from scripts.tezos.deploy_token import deploy_token_command
from scripts.tezos.deploy_router import deploy_router_command
from scripts.tezos.deploy_token_bridge_helper import deploy_token_bridge_helper_command
from scripts.tezos.xtz_deposit import xtz_deposit_command
from scripts.tezos.xtz_deposit_michelson import xtz_deposit_michelson_command
from scripts.tezos.execute_outbox_message import execute_outbox_message_command
from scripts.tezos.deploy_fast_withdrawal import deploy_fast_withdrawal_command
from scripts.tezos.build_contracts import (
    build_contracts_command as build_tezos_contracts_command,
)
from scripts.tezos.build_contracts import build_fast_withdrawal_command
from scripts.etherlink.fa_withdraw import fa_withdraw_command
from scripts.etherlink.xtz_withdraw import xtz_withdraw_command
from scripts.etherlink.xtz_fast_withdraw import xtz_fast_withdraw_command
from scripts.etherlink.deploy_erc20 import deploy_erc20_command
from scripts.etherlink.parse_withdrawal_event import parse_withdrawal_event_command
from scripts.etherlink.build_contracts import (
    build_contracts_command as build_etherlink_contracts_command,
)
from scripts.etherlink.test_contracts import test_contracts_command
from scripts.rollup_node.get_proof import get_proof_command
from scripts.rollup_node.scan_outbox import scan_outbox_command
from scripts.monitoring.deposits import monitor_deposits_command
from scripts.monitoring.withdrawals import monitor_withdrawals_command
from scripts.bootstrap.bootstrap import rollout_command
from scripts.bridge_token import bridge_token_command

# Every subcommand, registered flat under `bridge`.
ALL_COMMANDS: list[click.Command] = [
    fa_deposit_command,
    fa_withdraw_command,
    xtz_deposit_command,
    xtz_deposit_michelson_command,
    xtz_withdraw_command,
    xtz_fast_withdraw_command,
    bridge_token_command,
    deploy_token_command,
    deploy_ticketer_command,
    deploy_router_command,
    deploy_token_bridge_helper_command,
    deploy_erc20_command,
    deploy_fast_withdrawal_command,
    get_ticketer_params_command,
    execute_outbox_message_command,
    parse_withdrawal_event_command,
    get_proof_command,
    scan_outbox_command,
    build_tezos_contracts_command,
    build_fast_withdrawal_command,
    build_etherlink_contracts_command,
    test_contracts_command,
    monitor_deposits_command,
    monitor_withdrawals_command,
    rollout_command,
]


def _network_defaults(config: NetworkConfig) -> dict[str, Any]:
    """Maps the active network config onto the option names that carry a
    network/account default. The same dict is offered to every subcommand;
    Click applies only the keys a given command actually declares."""

    return {
        'tezos_private_key': config.accounts.l1_private_key,
        'tezos_rpc_url': config.network.l1_rpc_url,
        'smart_rollup_address': config.network.smart_rollup_address,
        'etherlink_private_key': config.accounts.l2_private_key,
        'etherlink_rpc_url': config.network.l2_rpc_url,
        'etherlink_rollup_node_url': config.network.rollup_rpc_url,
        'kernel_address': config.network.l2_kernel_address,
        'withdraw_precompile': config.network.l2_withdraw_precompile_address,
        'xtz_withdraw_precompile': config.network.l2_native_withdraw_precompile_address,
        'xtz_ticket_helper': config.native.l1_ticket_helper_address,
        'xtz_ticketer_address': config.native.l1_ticketer_address,
        'fast_withdrawal_contract': config.network.fast_withdrawal_contract,
    }


@click.group()
@click.pass_context
def bridge(ctx: click.Context) -> None:
    """Tezos <-> Etherlink FA token bridge CLI."""

    defaults = _network_defaults(load_network())
    ctx.default_map = {name: defaults for name in bridge.commands}


for _command in ALL_COMMANDS:
    bridge.add_command(_command)
