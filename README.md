# Etherlink Bridge

This repository showcases the implementation of a bridge between Tezos and Etherlink.

On the Tezos side, the implementation includes smart contracts written in CameLIGO. These contracts include a **Ticketer** for wrapping **FA1.2** and **FA2** tokens into tickets, and a **TicketHelper**, which enables users to transfer tickets without the currently unsupported **ticket_transfer** operation within the Tezos infrastructure. The testing and build stack for Tezos includes `poetry`, `pytezos`, and `pytest`.

For the Etherlink side, the repository provides solidity contracts, including the **ERC20Proxy**, which can be deployed on L2 to bridge tokens. The testing of Etherlink contracts is performed using `solidity`, utilizing the `foundry` stack for both testing and contract compilation.

The implementation adheres to the [TZIP-029](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md) standard.

## Project Structure:
* The [tezos](tezos/) directory houses contracts written in CameLIGO, along with associated tests utilizing the [pytezos](https://pytezos.org/) Python library. Additionally, the [tezos/build](tezos/build/) directory contains compiled contracts, simplifying the demonstration of interactions with the bridge process.
* The [etherlink](etherlink/) directory includes contracts and tests written in `solidity`. This directory also hosts contracts compiled with `foundry` located in the [etherlink/build](etherlink/build/) directory.
* The [`scripts`](scripts/) directory features Python scripts for interacting with the bridge. These scripts facilitate contract deployment on both sides of the bridge and enable the deposit and withdrawal of tickets via the bridge.

## Interact with bridge
The simplest way to run the notebook is by clicking [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/baking-bad/etherlink-bridge/blob/feat/scripts-and-docs/etherlink_bridge_demo.ipynb) to use Google Colab's cloud environment.
TODO: Replace the `feat/scripts-and-docs` branch with `main`.

Alternatively, user can clone this Git repository, follow the [installation guide](#install-dependencies), and set up environment variables with the following configurations:
- For Tezos: provide the node URL, rollup address, and private key for interacting with the Tezos side. The required variables are `L1_PRIVATE_KEY`, `L1_PUBLIC_KEY_HASH`, `L1_RPC_URL`, and `L1_ROLLUP_ADDRESS`.
- For Etherlink: provide the node URL, kernel address, withdrawal precompile address, and private key for interacting with the Etherlink side. The required variables are `L2_PRIVATE_KEY`, `L2_PUBLIC_KEY`, `L2_MASTER_KEY`, `L2_RPC_URL`, `L2_KERNEL_ADDRESS`, and `L2_WITHDRAW_PRECOMPILE_ADDRESS`.

To simplify the environment configuration, a script is provided to generate a `.env` file. This file will be used for interaction with the bridge. The script prompts the user to input the variable values needed.

Run the script using the following command:
```console
poetry run init_wallets
```

User may need to fund their Tezos and Etherlink accounts to execute this and subsequent scripts.
- To fund accounts on the Tezos side, use the Tezos [testnets faucet](https://faucet.nairobinet.teztnets.com/) (TODO: replace the faucet link with Ghostnet upon the bridge's activation in Ghostnet).
- To fund accounts on the Etherlink side, utilize the native token bridge (TODO: add a link to the native bridge, noting that it is not yet operational for our fork).

### Configuring the Bridge
Each bridge built on the TZIP-029 standard enables the transfer of tickets to a smart rollup. This process includes providing routing information, which facilitates the receipt of tokens on the L2 side. These tokens are minted by the ERC20 proxy contract.

As of the time this bridge was implemented, there were no ticket-native tokens on the Tezos side. Therefore, to bridge tokens, it is necessary to convert them into tickets using the **Ticketer**. Additionally, since the **transfer_ticket** operation is not yet implemented in wallets, a special **TicketHelper** is used. This helper wraps tokens into tickets and transfers them to the rollup in a single transaction.

To establish a bridge for an arbitrary token, the following steps should be taken:
- Deploy a **Ticketer** on the Tezos side for the specified **FA1.2** or **FA2** token.
- Deploy a **TicketHelper** on the Tezos side, targeting the specific token and **Ticketer** pair.
- Deploy an **ERC20Proxy** on the Etherlink side, configuring it to anticipate tickets from the given **Ticketer** with the specified payload.

#### Deploying a Token
For demonstration purposes, one can deploy a test token that will later be bridged. The bridge has been tested with two types of tokens in the repository:
- The **FA1.2** **Ctez** token.
- The **FA2** **fxhash** token.

To deploy this token and allocate the total supply to the token's originator, execute the following script. The example below illustrates the deployment for an **FA1.2** token type:
```console
poetry run deploy_token --token-type FA1.2
```
TODO: Add a link to the result of this operation in Nairobinet.

#### Deploying a Ticketer
To deploy a ticketer for a specific token address and token id, use the following script. The example below uses a **FA1.2** token previously deployed on Nairobinet:
```console
poetry run deploy_ticketer --token-address KT1XJ6ZbBE6MPmtYuNcFYo5oPYM4xsemxFwF --token-type FA1.2 --token-id 0
```
TODO: Add a link to the result of this operation in Nairobinet.

During **Ticketer** deployment user will receive **Ticketer** parameters, that will be required for **ERC20Proxy** origination: ticketer **address_bytes** and **content_bytes**.
During the Ticketer's deployment, user will receive its parameters, including **address_bytes** and **content_bytes**. These are required for the origination of the **ERC20Proxy**.

#### Deploying a Ticket Helper
To enable Tezos wallets to interact with specific tickets, deploy a Ticket Helper using the script below. The example provided uses a ticketer that was previously deployed in Nairobinet:
```console
poetry run deploy_ticket_helper --ticketer-address KT1MkNDvrW4V6TY2MU8RhHWDVHm5y3B1sn5m
```
TODO: Add a link to the result of this operation in Nairobinet.

#### Deploying ERC20Proxy
Finally, to deploy a token contract on the Etherlink side, which will mint tokens upon deposit, execute the script below. This script requires **ticketer-address-bytes** and **ticketer-content-bytes**. The example uses bytes from a ticketer previously deployed in Nairobinet:
```console
poetry run deploy_erc20 --ticketer-address-bytes 01906a4f54a7c9bc66c7c159f5ab7df90166acb02b00 --ticketer-content-bytes 0707000005090a0000005f05020000005907040100000010636f6e74726163745f616464726573730a0000001c050a0000001601f923adf742bdc1c3e14944859de0afa800f6b7a5000704010000000a746f6b656e5f747970650a0000000b0501000000054641312e32
```
TODO: Add a link to the result of this operation in blockscount.

NOTE: To obtain the **ticketer-address-bytes** and **content-bytes** for an already deployed ticketer, user can use the script below:
```
poetry run get_ticketer_params --ticketer-address KT1MkNDvrW4V6TY2MU8RhHWDVHm5y3B1sn5m
```

### Deposit
To make a deposit, user need to transfer Tickets to the rollup address with attached Routing Info in the [specified format](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#deposit). A script is available to facilitate this process. It requires the Ticket Helper address as **ticket-helper-address**, the Etherlink ERC20Proxy contract as **proxy-address**, and the bridged amount as the **amount** variable. Here's an example:
```console
poetry run deposit --ticket-helper-address KT1CXMcdSCw3sviupN6hwzzmfcyMYAF58W77 --proxy-address 0x6065534feE55f585C2d43f8e78BcE4C308EE066B --amount 42
```
NOTE: This script performs two operations in bulk. The first operation approves the token for the **Ticket Helper**, and the second operation makes a call to the **Ticket Helper** **deposit** entrypoint.

TODO: Add links to the results of this operation in Nairobinet AND Etherlink.

### Withdrawal Process
The withdrawal process involves two key steps:
1. Initiating the withdrawal on the Etherlink side, which results in the creation of an outbox message in the rollup commitment.
2. Completing the withdrawal by executing the outbox message on the Tezos side once the commitment has settled (TODO: Clarify terminology if necessary).

#### Etherlink Withdrawal
To initiate a withdrawal, user need to call the withdrawal precompile on the Etherlink side. This requires providing the **ERC20Proxy** address along with Routing Info in a [specific format](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#withdrawal). A script is available to facilitate the withdrawal process. It requires the ERC20 contract (which will burn tokens) as **proxy-address**, the Tezos router address (which will receive the ticket from the rollup) as **router-address**, and the bridged amount as **amount**. Additionally, the **ticketer-address-bytes** and **ticketer-content-bytes** are required to allow **ERC20Proxy** validate token before burning.

NOTE: For automatic unwrapping of Tezos tickets back into tokens, the **Ticketer** address can be provided as the **router-address**.

```console
poetry run withdraw --proxy 0x6065534feE55f585C2d43f8e78BcE4C308EE066B --amount --router KT1CXMcdSCw3sviupN6hwzzmfcyMYAF58W77 42 --ticketer-address-bytes 01906a4f54a7c9bc66c7c159f5ab7df90166acb02b00 --ticketer-content-bytes 0707000005090a0000005f05020000005907040100000010636f6e74726163745f616464726573730a0000001c050a0000001601f923adf742bdc1c3e14944859de0afa800f6b7a5000704010000000a746f6b656e5f747970650a0000000b0501000000054641312e32
```

TODO: Add links to the results of this operation in Etherlink.

#### Finalizing Tezos Withdrawal
To complete the withdrawal process, user need to call the outbox message on the Tezos side once it has been finalized (settled) on the L1 side. During the withdrawal process, the Etherlink side emits a **Withdrawal** event, which includes **outboxLevel** and **outboxMsgId**.

TODO: Provide a link to the Blockscout page featuring this event.
TODO: Explain how to parse this information.

To obtain the proof and commitment, use the following script:
```console
poetry get_proof --outbox-level ... --outbox-message-id ...
```

TODO: This script is not yet implemented.

For executing the outbox message, run:
```console
poetry execute_outbox_message --commitment ... --proof ...
```
TODO: This script is not yet implemented.

## Compilation and Running Tests
### Install Dependencies
1. If not already installed, install poetry using the following command:
```console
pip install poetry
```

2. Install all Python dependencies with:
```console
poetry install
```

3. Install Foundry by following the [installation guide](https://book.getfoundry.sh/getting-started/installation)

### Linting
To perform linting, execute the following commands:

```console
poetry run mypy .
poetry run ruff .
poetry run black .
```

### Tests
To run the tests, use the following commands:

1. For Tezos specific tests:
```console
poetry run pytest
```

2. For Etherlink specific tests:
```console
poetry run etherlink_tests
```

### Compilation
To compile the contracts, execute the following commands:

1. For building Tezos contracts:
```console
poetry run build_tezos_contracts
```

2. For building Etherlink contracts:
```
poetry run build_etherlink_contracts
```
