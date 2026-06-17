import click
from eth_abi import decode  # type: ignore
from web3.exceptions import ContractLogicError
from web3.types import HexBytes  # type: ignore
from scripts.helpers.utility import (
    get_etherlink_web3,
    get_etherlink_account,
)
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
    format_int,
    error,
)
from scripts.helpers.etherlink import FaWithdrawalPrecompileHelper
from scripts.networks import load_network
from scripts import cli_options


class ClaimError(click.ClickException):
    """An expected claim failure, shown as a red `Error: …` line."""

    def show(self, file: object = None) -> None:
        click.echo(error(f'Error: {self.format_message()}'), err=True)


erc20_proxy_option = click.option(
    '--erc20-proxy-address',
    default=None,
    help='ERC20 proxy (L2 token) to claim a deposit for. Defaults to the active '
    "network's default token.",
)

receiver_option = click.option(
    '--receiver-address',
    default=None,
    help='Narrow the latest queued deposit to this EVM receiver (e.g. a tz* alias). '
    'Ignored when --nonce is given.',
)

nonce_option = click.option(
    '--nonce',
    default=None,
    type=int,
    help='Claim this exact QueuedDeposit nonce instead of the latest for the token.',
)


def _revert_reason(exc: ContractLogicError) -> str | None:
    """Decode a Solidity `Error(string)` revert payload (selector 0x08c379a0)
    from a ContractLogicError, or None if it carries no standard string reason."""

    data = getattr(exc, 'data', None)
    if isinstance(data, (bytes, bytearray)):
        data = '0x' + bytes(data).hex()
    if not isinstance(data, str) or not data.startswith('0x08c379a0'):
        return None
    try:
        return str(decode(['string'], bytes.fromhex(data[10:]))[0])
    except Exception:
        return None


def fa_deposit_claim(
    erc20_proxy_address: str | None,
    receiver_address: str | None,
    nonce: int | None,
    withdraw_precompile: str,
    etherlink_private_key: str,
    etherlink_rpc_url: str,
) -> str:
    """Finalises a queued FA deposit by claiming its nonce on the FA bridge.

    The new kernel queues FA deposits; the L2 mint happens only once the
    deposit's `QueuedDeposit` nonce is claimed. By default this claims the
    newest queued deposit for the token (`--erc20-proxy-address`), optionally
    narrowed to `--receiver-address`. Pass `--nonce` to claim a specific one.
    If the nonce is already claimed, the claim transaction reverts.
    """

    erc20_proxy_address = erc20_proxy_address or load_network().default_erc20_proxy()
    if not erc20_proxy_address:
        raise ClaimError(
            'No --erc20-proxy-address given and the active network has no '
            'default token.'
        )

    web3 = get_etherlink_web3(etherlink_rpc_url)
    account = get_etherlink_account(web3, etherlink_private_key)
    precompile = FaWithdrawalPrecompileHelper.from_address(
        web3=web3,
        account=account,
        address=withdraw_precompile,
    )

    click.echo('Claiming FA deposit on bridge ' + wrap(accent(withdraw_precompile)) + ':')
    echo_variable('  - ', 'Executor', account.address)
    echo_variable('  - ', 'Etherlink RPC node', etherlink_rpc_url)
    echo_variable('  - ', 'ERC20 proxy (token)', erc20_proxy_address)

    if nonce is None:
        nonce = precompile.latest_queued_nonce_by_proxy(
            erc20_proxy_address, receiver_address
        )
        if nonce < 0:
            scope = f' for receiver {receiver_address}' if receiver_address else ''
            raise ClaimError(
                f'No QueuedDeposit found for token {erc20_proxy_address}{scope}.'
            )
        if receiver_address:
            echo_variable('  - ', 'Receiver', receiver_address)
        echo_variable('  - ', 'Latest queued nonce', format_int(nonce))
    else:
        echo_variable('  - ', 'Nonce', format_int(nonce))

    try:
        receipt = precompile.claim(nonce)
    except ContractLogicError as exc:
        reason = _revert_reason(exc)
        raise ClaimError(f'Claim of nonce {nonce} reverted: {reason or exc}')
    tx_hash: HexBytes = receipt.transactionHash  # type: ignore
    click.echo(
        'Successfully claimed FA deposit, tx hash: ' + wrap(accent(tx_hash.hex()))
    )
    return tx_hash.hex()


fa_deposit_claim_command = cli_options.command(
    fa_deposit_claim,
    name='fa_deposit_claim',
    options=[
        erc20_proxy_option,
        receiver_option,
        nonce_option,
        cli_options.withdraw_precompile,
        cli_options.etherlink_private_key,
        cli_options.etherlink_rpc_url,
    ],
)
