"""Offline CLI wiring tests.

Rendering a command's `--help` via Click's CliRunner exercises its option
registration without touching the network, catching wiring bugs mypy can't see
through Click: a default_map key that doesn't match an option's dest, a
duplicate/typo'd option, command-rename drift.

The commands are imported directly from their modules rather than via
`scripts.cli`, because the `bootstrap` command pulls in `survey`, which grabs
`sys.stdin.fileno()` at import time and fails under pytest's captured stdin.
`bootstrap` is therefore not covered here.
"""

import click
import pytest
from click.testing import CliRunner

from scripts.bridge_token import bridge_token_command
from scripts.etherlink.build_contracts import (
    build_contracts_command as build_etherlink_contracts_command,
)
from scripts.etherlink.deploy_erc20 import deploy_erc20_command
from scripts.etherlink.fa_withdraw import fa_withdraw_command
from scripts.etherlink.parse_withdrawal_event import parse_withdrawal_event_command

# aliased so pytest doesn't try to collect the `test_`-prefixed name as a test
from scripts.etherlink.test_contracts import (
    test_contracts_command as etherlink_tests_command,
)
from scripts.etherlink.xtz_fast_withdraw import xtz_fast_withdraw_command
from scripts.etherlink.xtz_withdraw import xtz_withdraw_command
from scripts.networks import load_network
from scripts.rollup_node.get_proof import get_proof_command
from scripts.rollup_node.scan_outbox import scan_outbox_command
from scripts.monitoring.deposits import monitor_deposits_command
from scripts.monitoring.withdrawals import monitor_withdrawals_command
from scripts.tezos.build_contracts import (
    build_contracts_command as build_tezos_contracts_command,
)
from scripts.tezos.build_contracts import build_fast_withdrawal_command
from scripts.tezos.deploy_fast_withdrawal import deploy_fast_withdrawal_command
from scripts.tezos.deploy_router import deploy_router_command
from scripts.tezos.deploy_ticketer import deploy_ticketer_command
from scripts.tezos.deploy_token import deploy_token_command
from scripts.tezos.deploy_token_bridge_helper import deploy_token_bridge_helper_command
from scripts.tezos.execute_outbox_message import execute_outbox_message_command
from scripts.tezos.fa_deposit import fa_deposit_command
from scripts.tezos.get_ticketer_params import get_ticketer_params_command
from scripts.tezos.xtz_deposit import xtz_deposit_command
from scripts.tezos.xtz_deposit_michelson import (
    michelson_routing_data,
    xtz_deposit_michelson_command,
)

COMMANDS = [
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
    etherlink_tests_command,
    monitor_deposits_command,
    monitor_withdrawals_command,
]


@pytest.mark.parametrize('cmd', COMMANDS, ids=lambda cmd: cmd.name)
def test_subcommand_help(cmd: click.Command) -> None:
    result = CliRunner().invoke(cmd, ['--help'])
    assert result.exit_code == 0, result.output
    assert 'Usage:' in result.output


def test_default_map_injects_option_default() -> None:
    # The `bridge` group feeds option defaults from the network config via
    # default_map; verify the mechanism reaches a real command's option (its
    # value shows up as the option default in --help).
    @click.group()
    @click.pass_context
    def group(ctx: click.Context) -> None:
        ctx.default_map = {
            name: {'smart_rollup_address': 'sr1-from-map'} for name in group.commands
        }

    group.add_command(fa_deposit_command)

    result = CliRunner().invoke(group, ['fa_deposit', '--help'])
    assert result.exit_code == 0
    assert 'sr1-from-map' in result.output


def test_private_key_default_not_leaked() -> None:
    # Private keys come from default_map too, but carry no show_default, so the
    # configured value must never appear in help output.
    result = CliRunner().invoke(fa_deposit_command, ['--help'])
    assert '--tezos-private-key' in result.output
    assert load_network().accounts.l1_private_key not in result.output


def test_michelson_routing_data() -> None:
    # Known-good vector: byte-reproduces the routing data of a real on-chain
    # Tezos X deposit.
    assert (
        michelson_routing_data('tz1KqTpEZ7Yob7QbPE4Hy4Wo8fHG8LhKxZSx').hex()
        == '01dad80196000002298c03ed7d454a101eb7022bc95f7e5f41ac78c0'
    )


def test_michelson_routing_data_rejects_originated() -> None:
    with pytest.raises(click.BadParameter):
        michelson_routing_data('KT1DUaf49SNALJRSB8R45TvEtgVi2xZnCh8B')
