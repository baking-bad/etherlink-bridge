from typing import Any, Callable, Optional, Sequence

import click
from click.core import (
    Context,
    Option,
)

# Network/account defaults come from the `bridge` group's per-network
# default_map (scripts/cli.py), so the options below carry no baked-in default.

# TODO: add validation to options? (reuse logic from bootstrap?)


def command(
    core: Callable[..., Any],
    *,
    name: str,
    options: Sequence[Callable[..., Any]],
) -> click.Command:
    """Builds a Click command from a plain typed `core` function and a list of
    option decorators. The thin wrapper forwards parsed options to `core`, so
    callers can invoke the fully typed `core` directly."""

    def wrapper(**kwargs: Any) -> Any:
        return core(**kwargs)

    wrapper.__doc__ = core.__doc__
    cmd = click.command(name=name)(wrapper)
    for option in options:
        option(cmd)
    return cmd


skip_confirm = click.option(
    '--skip-confirm',
    is_flag=True,
    default=False,
    help='Skip confirmation before deploying contracts.',
)

silent = click.option(
    '--silent',
    is_flag=True,
    default=False,
    help='Do not print any output.',
)

tezos_private_key = click.option(
    '--tezos-private-key',
    required=True,
    help='Private key that would be used to deploy contracts on the Tezos network.',
)

# TODO: consider renaming to `--tezos-rpc-node-url`
tezos_rpc_url = click.option(
    '--tezos-rpc-url',
    help='Tezos RPC shell URL',
    show_default=True,
)

token_address = click.option(
    '--token-address',
    required=True,
    prompt='Token contract address',
    help='The address of the FA token contract that should be bridged.',
    type=str,
)

token_type = click.option(
    '--token-type',
    required=True,
    help='Token type, either `FA2` or `FA1.2`.',
    type=click.Choice(['FA1.2', 'FA2'], case_sensitive=False),
)


def validate_token_id(ctx: Context, param: Option, value: Optional[str]) -> int:
    if value is None:
        if ctx.params['token_type'] == 'FA2':
            value = click.prompt('Token id in the contract')
        elif ctx.params['token_type'] == 'FA1.2':
            # NOTE: FA1.2 tokens don't have token id, consider returning None here
            return 0
        else:
            raise click.BadParameter('Invalid token type.')
    try:
        return int(value)
    except ValueError:
        raise click.BadParameter('Token id should be an integer.')


token_id = click.option(
    '--token-id',
    default=None,
    type=int,
    callback=validate_token_id,
    help='Identifier of the token in the contract (only for FA2).',
)

token_bridge_helper_address = click.option(
    # TODO: consider renaming to `--helper`
    '--token-bridge-helper-address',
    required=True,
    prompt='Token Bridge Helper address',
    help='The address of the Tezos Token Bridge Helper contract.',
)

smart_rollup_address = click.option(
    '--smart-rollup-address',
    required=True,
    show_default=True,
    help='The address of the Smart Rollup contract.',
)

etherlink_private_key = click.option(
    '--etherlink-private-key',
    help='Private key that would be used to deploy contract on the Etherlink network.',
)

# TODO: consider renaming to `--etherlink-rpc-node-url`
etherlink_rpc_url = click.option(
    '--etherlink-rpc-url',
    required=True,
    show_default=True,
    help='Etherlink RPC shell URL.',
)

etherlink_rollup_node_url = click.option(
    '--etherlink-rollup-node-url',
    required=True,
    show_default=True,
    help='Etherlink operator rollup node URL.',
)

kernel_address = click.option(
    '--kernel-address',
    show_default=True,
    help='The address of the Etherlink kernel which manages (mints and burns) bridged tokens.',
)

ticketer_address = click.option(
    '--ticketer-address',
    required=True,
    prompt='Ticketer contract address',
    help='The address of the Ticketer contract that wraps FA Token on Tezos side.',
)

tezos_side_router_address = click.option(
    '--tezos-side-router-address',
    required=True,
    prompt='Router contract address on Tezos side',
    help='The address of the Router proxy contract that routes tickets from Smart Rollup on Tezos side. Normally this is the address of the Ticketer contract.',
)

ticketer_address_bytes = click.option(
    '--ticketer-address-bytes',
    required=True,
    prompt='Ticketer address bytes',
    help='The address of the ticketer contract encoded in forged form: `| 0x01 | 20 bytes | 0x00 |`. See also `get_ticketer_params` command that helps with requesting and formatting this param for a given ticketer address.',
)

ticket_content_bytes = click.option(
    '--ticket-content-bytes',
    required=True,
    prompt='Ticket content bytes',
    help='The content of the ticket as micheline expression is in its forged form, **legacy optimized mode**. See also `get_ticket_params` command that helps with requesting and formatting this param for a given ticket address.',
)

withdraw_precompile = click.option(
    '--withdraw-precompile',
    show_default=True,
    help='The address of the FA Withdrawal Precompile contract.',
)

xtz_withdraw_precompile = click.option(
    '--xtz-withdraw-precompile',
    show_default=True,
    help='The address of the XTZ Withdrawal Precompile contract.',
)

erc20_proxy_address = click.option(
    '--erc20-proxy-address',
    required=True,
    prompt='ERC20 proxy address',
    help='The address of the ERC20 Proxy token on the Etherlink side in bytes form.',
)

token_decimals = click.option(
    '--token-decimals',
    required=True,
    type=int,
    prompt='Token decimals',
    help='Token decimals added to the ERC20 Proxy token and Ticketer metadata content.',
)

token_symbol = click.option(
    '--token-symbol',
    required=True,
    prompt='Token symbol',
    help='Token symbol added to the ERC20 Proxy token and Ticketer metadata content.',
)

token_name = click.option(
    '--token-name',
    required=True,
    prompt='Token name',
    help='Token name added to the ERC20 Proxy token and Ticketer metadata content.',
)

total_supply = click.option(
    '--total-supply',
    required=True,
    type=int,
    prompt='Total supply',
    help='Total supply of the token.',
)

amount = click.option(
    '--amount',
    required=True,
    type=int,
    prompt='Amount',
    help='The amount of tokens to be deposited or withdrawn.',
)

receiver_address = click.option(
    '--receiver-address',
    required=True,
    prompt='Receiver address',
    help='The address of the receiver of the tokens on another layer.',
)

xtz_ticket_helper = click.option(
    '--xtz-ticket-helper',
    show_default=True,
    help='The address of the xtz ticket helper used in xtz bridge.',
)
