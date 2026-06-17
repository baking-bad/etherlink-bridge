"""TEMPORARY — do not merge to main.

NAC (Michelson -> EVM) cross-runtime calls through the enshrined Tezos X
gateway `%call_evm`, plus the pytezos patches Tezos X needs. Used only by the
Michelson withdrawal commands (`xtz_withdraw_michelson`, `fa_withdraw_michelson`).

The patches are process-global; that's fine for a one-shot CLI invocation but is
why this lives apart from the regular `get_tezos_client`. See the long-form
rationale in `../../tezos-x/explore-with-pytz/prelude.py::load_tezos`.
"""

import math
import time
from typing import Any

import requests
from pytezos import pytezos
from pytezos.client import PyTezosClient
from pytezos.context.impl import ExecutionContext
from pytezos.operation import fees as _pytezos_fees
from pytezos.operation.group import OperationGroup
from pytezos.rpc.shell import PendingOperationsQuery

# Enshrined Michelson -> EVM gateway (KT1) and EVM-side bridge precompiles.
# Fixed kernel addresses, identical across Tezos X instances.
TEZOSX_GATEWAY = 'KT18oDJJKXMKhfE1bSuAPGp92pYcwVDiqsPw'
XTZ_BRIDGE = '0xff00000000000000000000000000000000000001'
FA_BRIDGE = '0xff00000000000000000000000000000000000002'


def _read_node_fee_config(rpc_url: str) -> dict[str, Any]:
    """Read minimal-fee thresholds from the node's mempool filter. Tezos X sets
    these below pytezos' hardcoded mainnet defaults, so without this low-gas ops
    get under-quoted and rejected with `insufficient_fees`."""

    response = requests.get(f'{rpc_url}/chains/main/mempool/filter', timeout=5)
    response.raise_for_status()
    filter_config = response.json()
    gas_num, gas_den = (int(x) for x in filter_config['minimal_nanotez_per_gas_unit'])
    byte_num, byte_den = (int(x) for x in filter_config['minimal_nanotez_per_byte'])
    return {
        'minimal_fees': int(filter_config['minimal_fees']),
        'minimal_mutez_per_gas_unit': (gas_num / gas_den) / 1000,
        # Round up so we never under-quote the per-byte component.
        'minimal_mutez_per_byte': math.ceil((byte_num / byte_den) / 1000),
    }


def patch_pytezos_for_tezosx(rpc_url: str) -> None:
    """Apply the process-global pytezos patches Tezos X needs.

    1. Stub the two call sites that hit `/chains/main/mempool/pending_operations`
       (404 on the Tezos X Michelson sequencer). Patched class-level because
       pytezos spawns fresh context/query instances per operation.
    2. Lower the module-level fee constants to the node's mempool-filter values.
    """

    ExecutionContext.get_counter_offset = lambda self: 0  # type: ignore[method-assign]
    PendingOperationsQuery.flatten = lambda self: []  # type: ignore[method-assign]
    fee_config = _read_node_fee_config(rpc_url)
    _pytezos_fees.MINIMAL_FEES = fee_config['minimal_fees']
    _pytezos_fees.MINIMAL_MUTEZ_PER_BYTE = fee_config['minimal_mutez_per_byte']
    _pytezos_fees.MINIMAL_MUTEZ_PER_GAS_UNIT = fee_config['minimal_mutez_per_gas_unit']


def get_michelson_l2_client(shell: str, key: str) -> PyTezosClient:
    """A patched pytezos client pointed at the Tezos X Michelson L2 sequencer."""

    patch_pytezos_for_tezosx(shell)
    client: PyTezosClient = pytezos.using(shell=shell, key=key)
    return client


def _wait_included(
    manager: PyTezosClient, opg_hash: str, attempts: int = 30, delay: int = 2
) -> None:
    """Poll recent blocks until the operation is included.

    Replaces pytezos `wait_operations`, whose `wait_blocks`/mempool polling is
    unreliable on the Tezos X sequencer — it gives up (StopIteration) before the
    op lands even though the op succeeds. `find_operation` is a plain level-scan
    with no block-timing dependency, so we drive the retry loop ourselves.
    """

    for _ in range(attempts):
        try:
            manager.shell.blocks[-20:].find_operation(opg_hash)
            return
        except StopIteration:
            time.sleep(delay)
    raise RuntimeError(
        f'Operation {opg_hash} was not found in recent blocks after '
        f'{attempts * delay}s — check the explorer.'
    )


def ensure_revealed(manager: PyTezosClient) -> str | None:
    """Reveal the account's public key if not already revealed, waiting for
    inclusion; return the reveal op hash, or None if it was already revealed.
    Tezos requires this one-time reveal before an account can originate ops."""

    public_key_hash = manager.key.public_key_hash()
    try:
        if manager.shell.contracts[public_key_hash].manager_key():
            return None
    except Exception:
        pass
    opg = manager.reveal().send()
    _wait_included(manager, str(opg.hash()))
    return str(opg.hash())


def nac_call_evm(
    manager: PyTezosClient,
    destination: str,
    method_sig: str,
    abi_params: bytes,
    amount_mutez: int = 0,
    callback: str | None = None,
) -> OperationGroup:
    """Build (and send) a `%call_evm` NAC call on the enshrined gateway.

    `call_evm` has type `pair string (pair string (pair bytes (option contract)))`
    = `(destination, method_sig, abi_params, callback?)`. The kernel derives the
    4-byte selector as `keccak256(method_sig)[:4]`, so `abi_params` is the
    ABI-encoded arguments only (no selector). `amount_mutez` is forwarded as the
    EVM `msg.value` (× 10^12 wei).
    """

    callback_value: dict[str, Any] = (
        {'prim': 'None'}
        if callback is None
        else {'prim': 'Some', 'args': [{'string': callback}]}
    )
    value = {
        'prim': 'Pair',
        'args': [
            {'string': destination},
            {
                'prim': 'Pair',
                'args': [
                    {'string': method_sig},
                    {
                        'prim': 'Pair',
                        'args': [{'bytes': abi_params.hex()}, callback_value],
                    },
                ],
            },
        ],
    }
    opg: OperationGroup = manager.transaction(
        destination=TEZOSX_GATEWAY,
        amount=amount_mutez,
        parameters={'entrypoint': 'call_evm', 'value': value},
    ).send()
    _wait_included(manager, str(opg.hash()))
    return opg
