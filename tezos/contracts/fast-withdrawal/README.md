# Fast Withdrawal Contract

This document provides an overview of the **Fast Withdrawal** contract - a component of the [Etherlink Bridge](https://docs.etherlink.com/bridging/bridging-tezos) designed to enable service providers to accept user withdrawals at a discounted rate. Providers pay the user immediately on Tezos and later reclaim the full amount when the Etherlink smart rollup finalizes the corresponding outbox message - typically after about two weeks on mainnet or ghostnet.

> [!IMPORTANT]
> Service providers must **fully trust their own data** from the Etherlink side because **any mistake** (like an incorrect timestamp or payload) **can lead to the provider losing their funds**. The Tezos smart contract verifies the data only at the moment it receives the outbox message from Etherlink. If parameters do not match exactly, **no reimbursement** will be delivered to the service provider.

## Table of Contents

1. [Overview](#overview)
2. [Entrypoints](#entrypoints)
   - [`payout_withdrawal`](#payout_withdrawal)
   - [`default`](#default)
   - [Views](#views)
3. [Parameters and Requirements](#parameters-and-requirements)
   - [Allowed and Disallowed Values](#allowed-and-disallowed-values)
   - [Why Accuracy Matters](#why-accuracy-matters)
4. [Compilation, Testing, and Deployment](#compilation-testing-and-deployment)
5. [Additional Notes](#additional-notes)

## Overview

The **Fast Withdrawal** feature enables a user to receive Tezos funds instantly from a service provider, long before the Etherlink outbox message is finalized. After about two weeks, Etherlink sends a corresponding ticket to the contract's `default` entrypoint to settle the withdrawal. If the provider paid out the user earlier (and correctly supplied all matching data), the provider gets reimbursed. Otherwise, the withdrawal is settled for the user directly.

The Fast Withdrawal process involves the following steps:
1. **User** triggers a withdrawal on Etherlink (L2).
2. **Provider** sees this event and decides to call `payout_withdrawal` on Tezos with the matching parameters, immediately sending funds to the user.
3. **Tezos contract** registers the claim in a local ledger.
4. **Two weeks later** (once the outbox message is cemented), the Tezos contract's `default` entrypoint is called with XTZ ticket, finalizing the withdrawal to the provider if a claim exists, or otherwise to the original user.

Here is a diagram showing these steps: [📄 Fast Withdrawal sequence diagram](../../../docs/fast-withdrawals-sequence.png)

## Entrypoints

### `payout_withdrawal`

`payout_withdrawal` is the entrypoint that **service providers** use to pay users instantly:

- **Parameters**:
  ```ocaml
    type payout_withdrawal_params = {
        withdrawal : {
            withdrawal_id : nat;
            full_amount : nat;
            ticketer : address;
            content : nat * bytes option;
            timestamp : timestamp;
            base_withdrawer : address;
            payload : bytes;
            l2_caller : bytes;
        };
        service_provider : address;
    }
  ```
  - `withdrawal`: The Fast Withdrawal event originating from Etherlink, represented by the corresponding outbox message.
  - `service_provider`: The Tezos address that will be reimbursed when the corresponding Etherlink outbox message is executed.

- **Behavior**:
  - Validates data, see: [Allowed and Disallowed Values](#allowed-and-disallowed-values)).
  - If all checks pass, the user (`base_withdrawer`) is paid immediately.
  - The contract records a claim in its ledger under the status `Paid_out(service_provider)`.

### `default`

`default` is the entrypoint used solely by the **Etherlink smart rollup** to finalize a withdrawal. It is the entrypoint that receives the outbox message:

- **Parameters**:
  ```ocaml
    type settle_withdrawal_params = {
        withdrawal_id : nat;
        ticket : (nat * bytes option) ticket;
        timestamp : timestamp;
        base_withdrawer : address;
        payload : bytes;
        l2_caller : bytes;
    }
  ```
- **Behavior**:
  - Verifies that the caller is indeed the Etherlink smart rollup.
  - Checks whether there is a matching claim from a service provider (`Paid_out` in the ledger).
  - If a claim exists, the contract changes its ledger state to `Cemented` and unwraps the incoming ticket in favor of the provider.
  - If no matching claim exists in the ledger, the contract unwraps the incoming ticket to the original `base_withdrawer`, and no updates are made to the ledger.

### Views

The contract also provides two views:
- `get_status`: Returns the status of a specific `withdrawal` (either `Paid_out <provider>`, `Cemented`, or `None` if unregistered).
- `get_config`: Returns the contract's configuration details (`xtz_ticketer`, `smart_rollup`, `expiration_seconds`).

## Parameters and Requirements

Below is a breakdown of the crucial parameters used in `payout_withdrawal`:

### Allowed and Disallowed Values

| Field                | Description                                                                                             | Allowed Values                                                                         | Disallowed Values / Constraints                                                                                                                  |
|----------------------|---------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| **`withdrawal_id`**      | A unique identifier for the withdrawal.                                                             | Any natural number (`nat`).                                                            | None (any `nat` is acceptable).                                                                                                                  |
| **`full_amount`**        | The full withdrawal amount as initiated on Etherlink (L2).                                          | Any natural number (`nat`).                                                            | None (any `nat` is acceptable).                                                                                                                  |
| **`ticketer`**           | Address of the XTZ ticketer contract that minted the ticket being withdrawn.                        | Must match the configured `xtz_ticketer` in the contract.                              | Any other address. The contract rejects non-matching `ticketer`s (no FA ticket support yet).                                                     |
| **`content`**            | The content of the XTZ ticket. For future FA compatibility.                                         | Must be `(0, None)`.                                                                   | Any other content.                                                                                                                               |
| **`timestamp`**          | The time when withdrawal was applied on Etherlink.                                                  | Must not be in the future relative to the Tezos chain time.                            | Values strictly greater than `Tezos.now()`.                                                                                                      |
| **`base_withdrawer`**    | The original Tezos address of the user who receives the XTZ withdrawal.                             | Any valid address on Tezos that can receive XTZ.                                       | Addresses that cannot receive XTZ (e.g., a `KT1` contract without a `default` entrypoint).                                                       |
| **`payload`**            | Michelson-encoded `nat` representing the discount payout amount.                                    | Must decode to a `nat`. The attached XTZ to `payout_withdrawal` must match this `nat`. | Non-decodable bytes, or mismatch between payload `nat` and attached XTZ.                                                                         |
| **`l2_caller`**          | Original Etherlink address in raw H160 form (20 bytes).                                             | Exactly 20 bytes in length.                                                            | Any length != 20 bytes.                                                                                                                          |

#### `service_provider`

- **Description**: The address that becomes the owner of the claim (`Paid_out(service_provider)`).
- **Constraints**: Must be able to receive XTZ.

### Why Accuracy Matters

There is no way to verify that a withdrawal actually occurred on the Etherlink side during the `payout_withdrawal` call on Tezos. As long as all formal checks pass, the contract will accept the `payout_withdrawal` transaction - even if no corresponding withdrawal with those parameters ever took place.

By calling `payout_withdrawal`, the service provider agrees to make an immediate payment to the `base_withdrawer` in exchange for a claim - a record stored in the contract's `withdrawals` ledger. This claim is uniquely identified by the `withdrawal` struct, which includes all the withdrawal parameters.

If **any** part of the `withdrawal` struct provided by the service provider does **not** exactly match the final outbox message from the Etherlink smart rollup (e.g., a mismatched `timestamp`, incorrect `withdrawal_id`, or inconsistent `payload`), then:

1. The settlement outbox message will **not** match the claim in the ledger, because the key differs.
2. The service provider will have already paid the user, but will **not** be reimbursed.

Therefore, it is **critical** to supply data that exactly matches what the Etherlink smart rollup will send during outbox message execution (withdrawal finalization). The safest approach is to extract this data directly from a rollup node's outbox messages, as they are already in the Micheline-encoded format expected by the Fast Withdrawal contract's `default` entrypoint.

## Compilation, Testing, and Deployment

> [!NOTE]
> See the [Setup instructions](../../../README.md#setup) to configure dependencies and enable Poetry-based commands.

Once you have set up the environment:

1. **Compile the Fast Withdrawal contract**:
   ```bash
   poetry run build_fast_withdrawal
   ```
2. **Run tests**:
   ```bash
   poetry run pytest tezos/tests/test_fast_withdrawal.py
   ```
3. **Deploy the contract**:
   - Via CLI script:
     ```bash
     poetry run deploy_fast_withdrawal
     ```
   - Or using the Jupyter notebook [scenario](../../../docs/scenarios/fast_withdrawals.ipynb) for a more guided approach:
     ```bash
     poetry run jupyter notebook docs/scenarios/fast_withdrawals.ipynb
     ```

## Additional Notes

- **Expiration Discount Logic**: The contract uses `expiration_seconds` to determine whether service providers are still eligible to make a payout at a discounted price (as defined by the `payload`-encoded amount). After the expiration period, the withdrawal can still be processed via `payout_withdrawal`, but the provider must pay the full withdrawal amount. While this removes any economic incentive for the provider, it ensures that users can still receive their funds before the two-week finalization - even if something goes wrong with the provider's services.
- **XTZ-Only**: Although the contract structure allows for potential FA Bridge tickets, it currently **rejects** all but native XTZ tickets.

> [!CAUTION]
> **Disclaimer**: This README is for **informational purposes only**. Use the Fast Withdrawal contract at your own risk. Make sure you fully understand its mechanics, the outbox finalization delays, and potential pitfalls concerning incorrect parameter values.
