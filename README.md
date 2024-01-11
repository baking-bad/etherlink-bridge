# Etherlink Bridge

This repository showcases the implementation of a bridge between Tezos and Etherlink.

On the Tezos side, the implementation includes smart contracts written in CameLIGO. These contracts include a **Ticketer** for wrapping **FA1.2** and **FA2** tokens into tickets, and a **TicketHelper**, which enables users to transfer tickets without the currently unsupported **ticket_transfer** operation within the Tezos infrastructure. The testing and build stack for Tezos includes `poetry`, `pytezos`, and `pytest`.

For the Etherlink side, the repository provides solidity contracts, including the **ERC20Proxy**, which can be deployed on L2 to bridge tokens. The testing of Etherlink contracts is performed using `solidity`, utilizing the `foundry` stack for both testing and contract compilation.

The implementation adheres to the [TZIP-029](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md) standard.

## Project Structure:
* The [tezos](tezos/) directory houses contracts written in CameLIGO, along with associated tests utilizing the [pytezos](https://pytezos.org/) Python library. Additionally, the [tezos/build](tezos/build/) directory contains compiled contracts, simplifying the demonstration of interactions with the bridge process.
* The [etherlink](etherlink/) directory includes contracts and tests written in `solidity`. This directory also hosts contracts compiled with `foundry` located in the [etherlink/build](etherlink/build/) directory.
* The [scripts](scripts/) directory features Python scripts for interacting with the bridge. These scripts facilitate contract deployment on both sides of the bridge and enable the deposit and withdrawal of tickets via the bridge.

## Interact with bridge
The simplest way to see how different parts of the bridge communicate with each other is to run the notebook by clicking [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/baking-bad/etherlink-bridge/blob/feat/scripts-and-docs/etherlink_bridge_demo.ipynb) to use Google Colab's cloud environment configured to run scripts from this repository.

TODO: Replace the `feat/scripts-and-docs` branch with `main`.

Alternatively, user can clone this Git repository, follow the [installation guide](#install-dependencies), and set up environment variables with the following configurations:
- For Tezos: provide the node URL, rollup address, and private key for interacting with the Tezos side. The required variables are `L1_PRIVATE_KEY`, `L1_PUBLIC_KEY_HASH`, `L1_RPC_URL`, and `L1_ROLLUP_ADDRESS`.
- For Etherlink: provide the node URL, kernel address, withdrawal precompile address, and private key for interacting with the Etherlink side. The required variables are `L2_PRIVATE_KEY`, `L2_PUBLIC_KEY`, `L2_MASTER_KEY`, `L2_RPC_URL`, `L2_ROLLUP_RPC_URL`, `L2_KERNEL_ADDRESS`, and `L2_WITHDRAW_PRECOMPILE_ADDRESS`.

To simplify the environment configuration, a script is provided to generate a `.env` file. This file will be used as a source of default variables for interaction with the bridge. The script prompts the user to input the variable values needed.

Run the script using the following command:
```shell
poetry run init_wallets
```

User may need to fund their Tezos and Etherlink accounts to execute this and subsequent scripts.
- To fund accounts on the Tezos side, use the Tezos [testnets faucet](https://faucet.nairobinet.teztnets.com/) (TODO: replace the faucet link with Ghostnet upon the bridge's activation in Ghostnet).
- To fund accounts on the Etherlink side, utilize the native token bridge (TODO: add a link to the native bridge, noting that it is not yet operational for our fork).

### Bridge Configuration (Listing New Token Pairs)
The **Ticket Transport Layer**, a key component of the bridge, enables ticket transfers between Tezos and Etherlink. To list a new token pair and establish a bridge, users need to:
1. If the token is an **FA2** or **FA1.2** standard token that doesn’t natively support tickets, the user must deploy a **Ticketer** contract on the Tezos side. This contract links to the specific Tezos token to convert it into a ticket.
2. The user then deploys an **ERC20Proxy** on the Etherlink side – a smart contract implementing ERC20. This contract should be configured to expect tickets from the deployed **Ticketer** including ticketer address and ticket content. This setup allows the rollup to mint ERC20 tokens corresponding to the incoming tickets from Tezos.
3. Additionally, deploy a **TicketHelper** on the Tezos side, targeting the specific token and **Ticketer** pair. This step is necessary as the **transfer_ticket** operation is not currently supported by wallets. The **TicketHelper** facilitates the wrapping of tokens into tickets and their transfer to the rollup in a single transaction.

#### Deploying a Token
For demonstration purposes, users can deploy a test token that will later be bridged. The bridge has been tested with two types of tokens, which are available in the repository:
- The **FA1.2** **Ctez** token.
- The **FA2** **fxhash** token.

To deploy this token and allocate the total supply to the token's originator, execute the following script. The example below illustrates the deployment for an **FA2** token type:
```shell
poetry run deploy_token --token-type FA2
```
Here is a link to the resulting operation in the [Nairobinet TzKT](https://nairobinet.tzkt.io/op7QGDUcdujMRSHq4C9MDcKwUus9mA2mrXQ15Vc4nsm1NSDJuMU/928446).

#### Deploying a Ticketer
To deploy a ticketer for a specific token address and token id, use the following script. The example below uses a **FA2** token previously deployed on Nairobinet:
```shell
poetry run deploy_ticketer --token-address KT1EMyCtaNPypSbz3qxuXmNZVfvhqifrf5MR --token-type FA2 --token-id 0
```
Here is a link to the resulting operation in the [Nairobinet TzKT](https://nairobinet.tzkt.io/ooVWNtZnUk2ZPiEaNh4daMQuyPQpdDV83x2BNxGZAT9BkSMwnd5/928447).

During the Ticketer's deployment, user will receive its parameters, including **address_bytes** and **content_bytes**. These are required for the origination of the **ERC20Proxy**.

#### Deploying a Ticket Helper
To enable Tezos wallets to interact with specific tickets, deploy a Ticket Helper using the script below. The example provided uses a ticketer that was previously deployed in Nairobinet:
```shell
poetry run deploy_ticket_helper --ticketer-address KT1MauRYJiXxD7a8iZkhpdnc4jHu7iGGXDbs
```
Here is a link to the resulting operation in the [Nairobinet TzKT](https://nairobinet.tzkt.io/opZqJve5nKFcNHuZ3YofhVspYnSNzPLo6WsWhor2Zg4nENUVDmM/928448).

#### Deploying ERC20Proxy
Finally, to deploy a token contract on the Etherlink side, which will mint tokens upon deposit, execute the script below. This script requires **ticketer-address-bytes** and **ticketer-content-bytes**. The example uses bytes from a ticketer previously deployed in Nairobinet:
```shell
poetry run deploy_erc20 --ticketer-address-bytes 018ea031e382d5be16a357753fb833e609c7d2dd9b00 --ticketer-content-bytes 0707000005090a0000007405020000006e07040100000010636f6e74726163745f616464726573730a0000001c050a00000016013f65105866518de12034c340e2b2f65d80780c580007040100000008746f6b656e5f69640a000000030500000704010000000a746f6b656e5f747970650a00000009050100000003464132 --token-name "FA2 Test Token" --token-symbol "FA2" --decimals 0
```
Here is a link to the resulting operation in the [Etherlink Blockscout](http://blockscout.dipdup.net/tx/0x41d7fc136882ef01a4497e9c9edec5b2fe05baa686c3d07199a432c65e181fc1).

NOTE: To obtain the **ticketer-address-bytes** and **content-bytes** for an already deployed ticketer, user can use the script below:
```shell
poetry run get_ticketer_params --ticketer KT1MauRYJiXxD7a8iZkhpdnc4jHu7iGGXDbs
```

### Deposit
To make a deposit, user need to transfer Tickets to the rollup address with attached Routing Info in the [specified format](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#deposit): `| receiver | proxy |` 40 bytes payload, both receiver and proxy are standard Ethereum addresses in raw form (H160). A script is available to facilitate this process. It requires the Ticket Helper address as **ticket-helper-address**, the Etherlink ERC20Proxy contract as **proxy-address**, and the bridged amount as the **amount** variable. Here's an example:
```shell
poetry run deposit --ticket-helper-address KT18nod2GU8PzYcrkspXz7dFkGisThZpgdLW --proxy-address 0x8554cD57C0C3E5Ab9d1782c9063279fA9bFA4680 --amount 777
```
Here is a link to the resulting operation in the [Nairobinet TzKT](https://nairobinet.tzkt.io/opRNngtr5dwYG6nJuXRAWXLPmE8Y17RgadwBQEtZfu3tfT9sxVv/928449) and [Etherlink Blockscout](http://blockscout.dipdup.net/tx/0xa34a41d8d5ca8e3019cb457c2a5b7f978ebf7193a72790fb6085b13ed2da1f66).

NOTE: This script performs two operations in bulk. The first operation approves the token for the **Ticket Helper**, and the second operation makes a call to the **Ticket Helper** **deposit** entrypoint.

### Withdrawal Process
The withdrawal process involves two key steps:
1. Initiating the withdrawal on the Etherlink side, which results in the creation of an outbox message in the rollup commitment.
2. Completing the withdrawal by executing the outbox message on the Tezos side once the commitment has settled (TODO: Clarify terminology if necessary).

#### Etherlink Withdrawal
To initiate a withdrawal, user need to call the withdrawal precompile on the Etherlink side. This requires providing the **ERC20Proxy** address along with Routing Info in a [specific format](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#withdrawal), two forged contracts concatenated: `| receiver | proxy |` 44 bytes. Forged contact consists of binary suffix/prefix and body (blake2b hash digest). A script is available to facilitate the withdrawal process. It requires the ERC20 contract (which will burn tokens) as **proxy-address**, the Tezos router address (which will receive the ticket from the rollup) as **router-address**, and the bridged amount as **amount**. Additionally, the **ticketer-address-bytes** and **ticketer-content-bytes** are required to allow **ERC20Proxy** validate token before burning.

NOTE: For automatic unwrapping of Tezos tickets back into tokens, the **Ticketer** address can be provided as the **router-address**.

```shell
poetry run withdraw --proxy-address 0x8554cD57C0C3E5Ab9d1782c9063279fA9bFA4680 --amount 108 --router-address KT1MauRYJiXxD7a8iZkhpdnc4jHu7iGGXDbs --ticketer-address-bytes 018ea031e382d5be16a357753fb833e609c7d2dd9b00 --ticketer-content-bytes 0707000005090a0000007405020000006e07040100000010636f6e74726163745f616464726573730a0000001c050a00000016013f65105866518de12034c340e2b2f65d80780c580007040100000008746f6b656e5f69640a000000030500000704010000000a746f6b656e5f747970650a00000009050100000003464132
```
Here is a link to the resulting operation in the [Etherlink Blockscout](http://blockscout.dipdup.net/tx/0xfc7e31241a44d3b23afdb41f5e69ecf4a8e3bc0e9f914039fe51beaa52400ed9).

#### Finalizing Tezos Withdrawal
To complete the withdrawal process, user need to call the outbox message on the Tezos side once it has been finalized (settled) on the L1 side. During the withdrawal process, the Etherlink side emits a **Withdrawal** event, which includes **outboxLevel** and **outboxMsgId**.

Users can obtain **outboxLevel** and **outboxMsgId** from the **Withdrawal** event, which is emitted upon the successful formation of an outbox message. Since both parameters are of type `uint256`, to retrieve **outboxMsgId**, users need to take the last 32 bytes of the event. For **outboxLevel**, take another 32 bytes preceding those and convert them into an integer. Below is an example of how this can be done:
- Here is a link to the block explorer with the withdrawal transaction: http://blockscout.dipdup.net/tx/0xfc7e31241a44d3b23afdb41f5e69ecf4a8e3bc0e9f914039fe51beaa52400ed9/logs
- Here is **Withdrawal** event data: `0x000000000000000000000000befd2c6ffc36249ebebd21d6df6376ecf3bac4480000000000000000000000008554cd57c0c3e5ab9d1782c9063279fa9bfa468000008a7390072a389159c73687165cd7910e8a39160600000000000000000000000000000000000000000000000000000000000000000000000000000000006c00000000000000000000000000000000000000000000000000000000002920a70000000000000000000000000000000000000000000000000000000000000000`
- Here is **outboxMsgId** is the last 32 bytes: `0000000000000000000000000000000000000000000000000000000000000000`, which is integer `0`
- Here is **outboxLevel** is the 32 bytes preceding those: `00000000000000000000000000000000000000000000000000000000002920a7`, which is integer `2695335`

To simplify this process, script to parse withdrawal event added:
```shell
poetry run parse_withdrawal_event --tx-hash 0xfc7e31241a44d3b23afdb41f5e69ecf4a8e3bc0e9f914039fe51beaa52400ed9
```

Now, when the user knows the index and outbox level where withdrawal transaction was added, it is possible to get **commitment** and **proof**, which are required for `execute_outbox_message` call. To do this users need to perform call to the `global/block/head/helpers/proofs/outbox/{outbox_level}/messages` Rollup RPC Node endpoint. There is a script which performs this call:
```shell
poetry run get_proof --level 2695335 --index 0
```

Since this outbox message settled on the L1 side, user able to execute it by making `execute_outbox_message` operation. There is a script which allows to do this using provided private keys, here is an example using commitment and proof for our test **FA2** token withdrawal:
```shell
poetry run execute_outbox_message --commitment src12xZPCATqCQ2yEwTsdjpUrZB3j5N4QEG2yE9ooKRkdebUoNnaVc --proof 03000246e559d1e67da67d8a58ba6336b2d0d590d907575b62bcb6f74b72a173fa1c4346e559d1e67da67d8a58ba6336b2d0d590d907575b62bcb6f74b72a173fa1c430005820764757261626c65d0e7d0dd265b0311f278277c7074a59f1e0ccd0eea95480712a8d16f2af2a5fd4803746167c00800000004536f6d650003c0eddd502da06bf12e3f51c320a2ae3e57ea25f85715bb937694c028196f5d4b40820576616c7565810370766d8107627566666572738205696e707574820468656164c00100066c656e677468c00100066f75747075740004820132810a6c6173745f6c6576656cc004002922470133810f76616c69646974795f706572696f64c00400013b0082013181086f7574626f786573010c0801061ec0b2503e758887e4c8867c03d8ee9fed3affd91be8d51b5c009fdc05dcf006c5220102ff01019500c30056c0284323d54769eace77824173c277fd6b0afc488e0c8793892d4ff56e6182445b0031c0641f1aec15551f28800a5b143a5138c20c32a6a79567e76121a03a34d7518c700019000d0009000700040004c092fc55432b8d1bb592f64e30bf689ca79cd662da42f5fa158742a5beefbe3108820732363933373233820468656164c00100066c656e677468c0010007323639353333350003810468656164c001008208636f6e74656e7473810130c0e9000000e500000000e007070a0000001600008a7390072a389159c73687165cd7910e8a39160607070a00000016018ea031e382d5be16a357753fb833e609c7d2dd9b0007070707000005090a0000007405020000006e07040100000010636f6e74726163745f616464726573730a0000001c050a00000016013f65105866518de12034c340e2b2f65d80780c580007040100000008746f6b656e5f69640a000000030500000704010000000a746f6b656e5f747970650a0000000905010000000346413200ac01018ea031e382d5be16a357753fb833e609c7d2dd9b00000000087769746864726177066c656e677468c00101e0c0fbeb6f8dbed945498bb241f2aa59b61fa41ce8f4183e87a0fb207bad530de545c0928d01251fe92a323735aad221c34a984287441f9928653781aae2ba3e1ed20ec01c04d9bbd31a532e2b64f2cea68d299bc3588607b6f3301b337a382751891ff4c0edb46d89cd791d0ba42b375b963b2d3519d61f7e6b9ad7acad6836ded1b00aa9c0aec97545fa52e4fd6d81eb6616fa7c32d86ab299b2842f8f47094e69f409ebc8c0f233f9b7aaf566f55bf84c6a0d0aaa4466f24838bc9fdf8feff9cb589906a07bc0031742da1992a697d7ad87911a3c08b7ece1bd4ee8f2ff458f2ddcc75ec2e2b5c02bd0fc4984cea88f93335810d338afcea380f16c6273a48ec617f755730319e20134810d6d6573736167655f6c696d6974c002a401047761736dd07a5feea7b7245822330d8f990fd24bf317c760800acf697a8e9289b16b05222b46e559d1e67da67d8a58ba6336b2d0d590d907575b62bcb6f74b72a173fa1c43002920a70000000000e007070a0000001600008a7390072a389159c73687165cd7910e8a39160607070a00000016018ea031e382d5be16a357753fb833e609c7d2dd9b0007070707000005090a0000007405020000006e07040100000010636f6e74726163745f616464726573730a0000001c050a00000016013f65105866518de12034c340e2b2f65d80780c580007040100000008746f6b656e5f69640a000000030500000704010000000a746f6b656e5f747970650a0000000905010000000346413200ac01018ea031e382d5be16a357753fb833e609c7d2dd9b00000000087769746864726177
```
Here is a link to the resulting operation in the [Nairobinet TzKT](https://nairobinet.tzkt.io/ongZVuFZmLaGNfF7zgMvufEE8APxAwoq7pbRv5GuJXdnqXgJZKh/928451).

## Compilation and Running Tests
### Install Dependencies
1. If not already installed, install poetry using the following command:
```shell
pip install poetry
```

2. Install all Python dependencies with:
```shell
poetry install
```

3. Install Foundry by following the [installation guide](https://book.getfoundry.sh/getting-started/installation)

### Linting
To perform linting, execute the following commands:

```shell
poetry run mypy .
poetry run ruff .
poetry run black .
```

### Tests
To run the tests, use the following commands:

1. For Tezos specific tests:
```shell
poetry run pytest
```

2. For Etherlink specific tests:
```shell
poetry run etherlink_tests
```

### Compilation
To compile the contracts, execute the following commands:

1. For building Tezos contracts:
```shell
poetry run build_tezos_contracts
```

2. For building Etherlink contracts:
```shell
poetry run build_etherlink_contracts
```
