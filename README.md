# Etherlink Bridge

This repository showcases the implementation of a bridge between Tezos and Etherlink based on the [TZIP-029](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md) standard.

On the Tezos side, there are smart contracts written in CameLIGO (TODO: add link to the LIGO project), including:
- [**Ticketer**](tezos/contracts/ticketer/ticketer.mligo) allowing wrapping **FA1.2** and **FA2** tokens into tickets, which can be sent to the bridge utilizing permissionless ticket transport,
- [**TicketHelper**](tezos/contracts/ticket-helper/ticket-helper.mligo), which enables users to transfer tickets without the currently unsupported **ticket_transfer** operation within the Tezos infrastructure.

For the Etherlink side, there are solidity contracts, including the **ERC20Proxy**: a ERC20 contract, which impelements L2 proxy [deposit interface](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#l2-proxy-deposit-interface) and [withdraw interface](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#l2-proxy-withdraw-interface) allowing to bridge tickets from L1.

TODO: Replace TZIP link branch with `main` when TZIP approved, multiple urls in the document.

The is also [scripts](scripts/) directory which features Python scripts, allowing interactions with the bridge: contract deployment on both sides of the bridge, deposit and withdrawal.

The simplest way to interact with components, run scripts and see how different parts of the bridge communicate with each other is to run demo notebook which is configured to be executed in the Google Colab's cloud environment: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/baking-bad/etherlink-bridge/blob/feat/scripts-and-docs/etherlink_bridge_demo.ipynb).

TODO: Replace the `feat/scripts-and-docs` branch with `main`.

Alternatively, user can clone this Git repository, follow the [installation guide](#install-dependencies), and set up environment by running:
```shell
poetry run init_wallets
```
This script will ask user to provide their Tezos and Etherlink private and public keys, along with ability to configure node for L1 and L2 communication. Default values are provided, testnet keys are included.

User may need to fund their Tezos and Etherlink accounts to execute scripts that interacts with L1 and L2 sides.
- To fund accounts on the Tezos side, use the Tezos [testnets faucet](https://faucet.nairobinet.teztnets.com/) (TODO: replace the faucet link with Ghostnet upon the bridge's activation in Ghostnet).
- To fund accounts on the Etherlink side, utilize the native token bridge (TODO: add a link to the native bridge, noting that it is not yet operational for our fork).

### Bridge Configuration (Listing New Token Pairs)
To configure the bridge for a new token (to list a new token pair), user must utilize the **Ticket Transport Layer**, a key component of the bridge, which enables ticket transfers between Tezos and Etherlink.

TODO: add some graphics, picture how this bridge works

The **FA2** and **FA1.2** standard Tezos tokens are non ticket-native, so to establish a bridge for these tokens, user first must deploy a **Ticketer** contract on the Tezos side. This contract links to the specific Tezos token to convert it into a ticket. This contract would not be required for the tokens which implement ticket-native standards (for example **FA2.1**).

NOTE: Ticketer contract upgrades are highly unwanted, ideally it is deployed once and forever.

After this is clear, which kind of tickets will be used to bridge token to the Etherlink, user able to deploy an **ERC20Proxy** – an ERC20 token with bridge L2 deposit and withdraw interfaces. This contract should be configured to expect tickets from the **Ticketer** deployed in the first step, including ticketer address and ticket content. This setup allows the rollup kernel to mint ERC20 tokens corresponding to the incoming tickets from Tezos.

Additionally, a **TicketHelper** on the Tezos side needs to be deployed, targeting the specific **Token** and **Ticketer** pair. This step is necessary as the **transfer_ticket** operation is not currently supported by wallets. The **TicketHelper** facilitates the wrapping of tokens into tickets and their transfer to the rollup in a single transaction. This kind of contract might be deprecated in the future, when (1) wallets start to support **transfer_ticket** operation, (2) Tezos receives protocol upgrade, allowing implicit address to transfer tickets with arbituary data.

#### Deploying a Token
For demonstration purposes, users can deploy a test token that will later be bridged. The bridge has been tested with two types of tokens, which are available in the repository:
- The **FA1.2** **Ctez** token.
- The **FA2** **fxhash** token.

To deploy this token and allocate the total supply to the token's originator, there is `deploy_token` command which have the following params: `--token-type`, `--token-id`, `--total-supply` and others. The example below illustrates the deployment for an **FA2** token type with default params:
```shell
poetry run deploy_token --token-type FA2
```
Here is a link to the resulting operation in the [Nairobinet TzKT](https://nairobinet.tzkt.io/op7QGDUcdujMRSHq4C9MDcKwUus9mA2mrXQ15Vc4nsm1NSDJuMU/928446).

#### Deploying a Ticketer
To deploy a ticketer for a specific token, there is `deploy_ticketer` command which requires `--token-address`, `--token-type` and `--token-id` parameters to be provded. The example below allows to deploy a ticketer for the **FA2** token that was previously deployed on Nairobinet:
```shell
poetry run deploy_ticketer --token-address KT1EMyCtaNPypSbz3qxuXmNZVfvhqifrf5MR --token-type FA2 --token-id 0
```
Here is a link to the resulting operation in the [Nairobinet TzKT](https://nairobinet.tzkt.io/ooVWNtZnUk2ZPiEaNh4daMQuyPQpdDV83x2BNxGZAT9BkSMwnd5/928447).

During the Ticketer's deployment, user will receive its parameters, including **address_bytes** and **content_bytes**. These are required for the origination of the **ERC20Proxy**.

#### Deploying a Ticket Helper
To enable Tezos wallets to interact with specific tickets, user needs to deploy a Ticket Helper using the `deploy_ticket_helper` command. It requires `--ticketer-address` to be provided and then the Ticketer storage parsed to get information about token. The example provided below deploys a ticket helper for the ticketer that was previously deployed in Nairobinet:
```shell
poetry run deploy_ticket_helper --ticketer-address KT1MauRYJiXxD7a8iZkhpdnc4jHu7iGGXDbs
```
Here is a link to the resulting operation in the [Nairobinet TzKT](https://nairobinet.tzkt.io/opZqJve5nKFcNHuZ3YofhVspYnSNzPLo6WsWhor2Zg4nENUVDmM/928448).

#### Deploying ERC20Proxy
Finally, to deploy a token contract on the Etherlink side, which will mint tokens upon deposit, `deploy_erc20` command provided. This script requires `--ticketer-address-bytes` and `--ticketer-content-bytes` along with `--token-name`, `--token-symbol` and `--decimals` to be provided to properly configure L2 token contract. The example below uses bytes from the ticketer which was previously deployed in Nairobinet:
```shell
poetry run deploy_erc20 --ticketer-address-bytes 018ea031e382d5be16a357753fb833e609c7d2dd9b00 --ticketer-content-bytes 0707000005090a0000007405020000006e07040100000010636f6e74726163745f616464726573730a0000001c050a00000016013f65105866518de12034c340e2b2f65d80780c580007040100000008746f6b656e5f69640a000000030500000704010000000a746f6b656e5f747970650a00000009050100000003464132 --token-name "FA2 Test Token" --token-symbol "FA2" --decimals 0
```
Here is a link to the resulting operation in the [Etherlink Blockscout](http://blockscout.dipdup.net/tx/0x41d7fc136882ef01a4497e9c9edec5b2fe05baa686c3d07199a432c65e181fc1).

NOTE: To obtain the **ticketer-address-bytes** and **content-bytes** for an already deployed ticketer, user can use the script below:
```shell
poetry run get_ticketer_params --ticketer KT1MauRYJiXxD7a8iZkhpdnc4jHu7iGGXDbs
```

### Deposit
To make a deposit, user need to transfer Tickets to the rollup address with attached Routing Info in the [specified format](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#deposit): `| receiver | proxy |` 40 bytes payload, both receiver and proxy are standard Ethereum addresses in raw form (H160). A command `deposit` is available to facilitate this process. It requires the Ticket Helper address as `--ticket-helper-address`, the Etherlink ERC20Proxy contract as `--proxy-address`, and the bridged amount as the `--amount` parameters to be set. Here's an example:
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

To simplify creation of this operation, there is `withdraw` command, which requires `--proxy-address`, `--amount`, `--ticketer-address-bytes`, `--ticketer-content-bytes` to be provided. Here is an example:
```shell
poetry run withdraw --proxy-address 0x8554cD57C0C3E5Ab9d1782c9063279fA9bFA4680 --amount 108 --ticketer-address-bytes 018ea031e382d5be16a357753fb833e609c7d2dd9b00 --ticketer-content-bytes 0707000005090a0000007405020000006e07040100000010636f6e74726163745f616464726573730a0000001c050a00000016013f65105866518de12034c340e2b2f65d80780c580007040100000008746f6b656e5f69640a000000030500000704010000000a746f6b656e5f747970650a00000009050100000003464132
```
Here is a link to the resulting operation in the [Etherlink Blockscout](http://blockscout.dipdup.net/tx/0xfc7e31241a44d3b23afdb41f5e69ecf4a8e3bc0e9f914039fe51beaa52400ed9).

#### Finalizing Tezos Withdrawal
To complete the withdrawal process, user needs to call the outbox message once it has been finalized (settled) on the Tezos side. To do this, user first required to aquire **commitment** hash and **proof** bytes, which can be requested from the rollup node by **outboxLevel** and **outboxMsgId**. And those parameters are part of the **Withdrawal** event, emitted during withdrawal process on the Etherlink side.

Since both parameters **outboxLevel** and **outboxMsgId** are of type `uint256`, to retrieve **outboxMsgId**, users need to take the last 32 bytes of the **Withdrawal** event logs. For **outboxLevel**, users need to take another 32 bytes preceding those and convert them both into an integers. Below is an example of how this can be done:
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
#### 1. Tezos side:
The testing stack for Tezos contracts based on Python and requires [poetry](TODO: add link), [pytezos](https://pytezos.org/), and [pytest](TODO: add link) to be installed.

To run tests for the Tezos contracts, execute:
```shell
poetry run pytest
```

#### 2. Etherlink side:
TODO: describe that `foundry` need to be installed for testing contracts.

The testing of Etherlink contracts is performed using `solidity`, utilizing the `foundry` stack. To run these tests either enter the [etherlink](etherlink/) directory and execute `forge test`, either execute the following script from the root directory:
```shell
poetry run etherlink_tests
```

### Compilation
To compile the contracts, execute the following commands:

#### 1. Tezos side:
TODO: describe that LIGO need to be installed, that docker is easiest option and to run LIGO compilation from docker there is command provided:

TODO: also add that there is option to select version and the contracts are written in LIGO v...

For building Tezos contracts, run following script:
```shell
poetry run build_tezos_contracts
```
NOTE: This repository includes builded Tezos side contracts which located in the [tezos/build](tezos/build/) directory.

#### 2. Etherlink side:
TODO: describe that `foundry` need to be installed for script building 
To run compilation either enter the [etherlink](etherlink/) directory and execute `forget build` or run the following script from the root directory:
```shell
poetry run build_etherlink_contracts
```
NOTE: This repository includes builded Etherlink side contracts which located in the [etherlink/build](etherlink/build/) directory.
