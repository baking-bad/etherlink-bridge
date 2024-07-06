### Bridge configuration
To configure the bridge for a new token (i.e., to list a new token pair), users need to engage with the **Ticket Transport Layer**. This critical component of the bridge facilitates the transfer of tickets between Tezos and Etherlink.

![permissionless ticket transfer short illustration](permissionless-ticket-transfer.png)

The **FA2** and **FA1.2** standard Tezos tokens are not inherently ticket-native. Therefore, to bridge these tokens, users must initially convert them to tickets. To do this they first need to deploy a **Ticketer** contract on the Tezos side. This contract will be associated with the specific Tezos token and provide entrypoint to wrap them into tickets. This contract is unnecessary for the forthcoming tokens that are ticket-native, such as those following the **FA2.1** standard.

NOTE: Upgrades to the Ticketer contract are highly unwanted because this will lead to liquidity fragmentation. Ideally, it should be deployed once and remain unchanged indefinitely.

Once it's determined what **Ticketer** will represent the token, users can deploy an **ERC20 Proxy** – an ERC20 token integrated with bridge deposit and withdrawal interfaces. The Ticketer address and ticket content are provided to the ERC20Proxy constructor during origination to bind the L2 token to the L1 ticket. It is also required to provide rollup kernel address to the ERC20 proxy which will be allowed to mint and burn tokens which is the `0x00` address.

Additionally, deploying a **Token Bridge Helper** on the Tezos side is required. This contract should be configured with specific **Token** and **Ticketer** contracts on the L1 side and **ERC20 Proxy** address on the L2 side. This contract is required for wallets that do not support the **transfer_ticket** operation. The **TokenBridgeHelper** wraps tokens into tickets and transfers tickets to the rollup in a single transaction. **Token Bridge Helper** is expected to become obsolete in the future when (1) wallets begin supporting the **transfer_ticket** operation and (2) Tezos undergoes a protocol upgrade that permits implicit addresses to transfer tickets with arbitrary data.

#### Deploying a Token
The bridge has been tested with two slightly changed tokens from the Mainnet, that are available in the repository:
- The **FA1.2** standard **Ctez** token.
- The **FA2** standard **fxhash** token.

To deploy a test version of a token and allocate the total supply to the token's originator, the `deploy_token` command can be used. The following example demonstrates how to deploy an **FA1.2** token:
```shell
poetry run deploy_token \
    --token-type FA1.2 \
    --total-supply 1000
```
Here is an example of the deployed [token](https://parisnet.tzkt.io/KT19P1nbGzGnumMfRHcLNuyQUdcuwjpBfsCU/operations/).

#### Deploying a Ticketer
The `deploy_ticketer` command can be used to deploy a ticketer configured for a specific token. It requires token parameters and metadata to be provided. Below is an example:
```shell
poetry run deploy_ticketer \
    --token-address KT19P1nbGzGnumMfRHcLNuyQUdcuwjpBfsCU \
    --token-type FA1.2 \
    --token-decimals 6 \
    --token-symbol "TST" \
    --token-name "Test Token"
```
Here is an example of the deployed [ticketer](https://parisnet.tzkt.io/KT1KjXCapuLqYjHjV6Ce7Mfsm7uiqRZY3Vw8/metadata/).

After the Ticketer contract is deployed, it is possible to obtain the parameters required for the **ERC20 Proxy** origination: **ticketer-address_bytes** and **content_bytes**. To do this, execute the `get_ticketer_params` command:
```shell
poetry run get_ticketer_params \
    --ticketer-address KT1KjXCapuLqYjHjV6Ce7Mfsm7uiqRZY3Vw8
```

For example, the ticketer deployed in the previous step has the following parameters:
```
Ticketer params:
  - Address bytes: `0x017a5122c4d13e36260501762df3621dc2b4b6f97d00`
  - Content bytes: `0x0707000005090a000000a505020000009f07040100000010636f6e74726163745f616464726573730a000000244b54313950316e62477a476e756d4d665248634c4e75795155646375776a70426673435507040100000008646563696d616c730a0000000136070401000000046e616d650a0000000a5465737420546f6b656e0704010000000673796d626f6c0a000000035453540704010000000a746f6b656e5f747970650a000000054641312e32`
  - Ticket hash: `0x29443976450593165867480032002089594521193528945155325239252958376738540795164`
```

#### Deploying ERC20 Proxy
Then, to deploy a token contract on the Etherlink side, the `deploy_erc20` command can be used. Below is an example:
```shell
poetry run deploy_erc20 \
    --ticketer-address-bytes 0x017a5122c4d13e36260501762df3621dc2b4b6f97d00 \
    --ticket-content-bytes 0x0707000005090a000000a505020000009f07040100000010636f6e74726163745f616464726573730a000000244b54313950316e62477a476e756d4d665248634c4e75795155646375776a70426673435507040100000008646563696d616c730a0000000136070401000000046e616d650a0000000a5465737420546f6b656e0704010000000673796d626f6c0a000000035453540704010000000a746f6b656e5f747970650a000000054641312e32 \
    --token-name "Test Token" \
    --token-symbol "TST" \
    --token-decimals 0
```
Here is an example of the deployed [token](http://blockscout.dipdup.net/address/0x03E39FF2b379FBcd9284Ab457113D82fF4daBBF4).

#### Deploying a Token Bridge Helper
Finally, to allow the interaction of Tezos wallets with tickets, it is required to deploy a **Token Bridge Helper**. During origination, Token Bridge Helper bounds to the Token, Ticketer and ERC20Proxy. To originate Token Bridge Helper user should run the `deploy_token_bridge_helper` command:
```shell
poetry run deploy_token_bridge_helper \
    --ticketer-address KT1KjXCapuLqYjHjV6Ce7Mfsm7uiqRZY3Vw8 \
    --erc20-proxy-address 0x22565c35Ad439cbb8399bfC733c56C9F5A10E3a6 \
    --token-symbol "TST"
```
Here is an example of the deployed [helper](https://parisnet.tzkt.io/KT1KbJTnQxV7s8q5bfzrJricA7HLEEqFzQnN/metadata).

### Deposit
To deposit a token, it should be wrapped into a ticket and then transferred to the smart rollup address, along with routing info provided in the [specified format](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#deposit): a 40-byte payload comprising `| receiver | proxy |`. The Token Bridge Helper contract allows users to perform these operations in one call using the `deposit` command:
```shell
poetry run deposit \
    --token-bridge-helper-address KT1KbJTnQxV7s8q5bfzrJricA7HLEEqFzQnN \
    --amount 37 \
    --receiver-address 0x7e6f6CCFe485a087F0F819eaBfDBfb1a49b97677 \
    --smart-rollup-address sr1HpyqJ662dWTY8GWffhHYgN2U26funbT1H
```
Here are examples of these operations on the [Tezos](https://parisnet.tzkt.io/onwj8usqmb1snvh35jzzsvxgM7U5rKazpz78pCEws12VLAaY8GW/16767) and [Etherlink](http://blockscout.dipdup.net/tx/0x29a281a68f50cc43e0c1af17f2e492d266c232d100403eca722d89c80c860d81) sides.

### Withdrawal Process
The withdrawal process consists of two steps:
1. Initiating the withdrawal on the Etherlink side by calling FA Withdrawal Precompile which then creates an outbox message from Etherlink to Tezos.
2. Finalizing the withdrawal on the Tezos side after the commitment was settled by executing the outbox message.

#### Etherlink Withdrawal
To initiate a withdrawal on the Etherlink side, users must invoke the **Withdrawal Precompile**. An **ERC20 Proxy** address as a ticket owner along with routing info should be provided. The [specified format](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#withdrawal) of the routing info is a 44-byte concatenation of two forged contracts: `| receiver | proxy |`.

To demonstrate this operation, the `withdraw` command is provided:
```shell
poetry run withdraw \
    --erc20-proxy-address 0x22565c35Ad439cbb8399bfC733c56C9F5A10E3a6 \
    --amount 18 \
    --ticketer-address-bytes 0x016439a915319865730848cc0130ec2cf553ea691500 \
    --ticket-content-bytes 0x0707000005090a000000b30502000000ad07040100000010636f6e74726163745f616464726573730a000000244b54314237596f4432706f6b5a4d415379744c3878336f5832693431464234647273424207040100000008646563696d616c730a0000000138070401000000046e616d650a0000000e5465737420747a425443207631380704010000000673796d626f6c0a0000000d544553545f747a4254435f31380704010000000a746f6b656e5f747970650a000000054641312e32 \
    --tezos-side-router-address KT1KjXCapuLqYjHjV6Ce7Mfsm7uiqRZY3Vw8 \
    --receiver-address tz1ekkzEN2LB1cpf7dCaonKt6x9KVd9YVydc
```

> NOTE: `--ticketer-address-bytes` and `--ticketer-content-bytes` are required to be provided to the **Withdrawal Precompile** so the **ERC20 Proxy** can validate the token before burning it.

> NOTE: The **Ticketer** implements a [L1 proxy withdraw router interface](https://gitlab.com/baking-bad/tzip/-/blob/wip/029-etherlink-token-bridge/drafts/current/draft-etherlink-token-bridge/etherlink-token-bridge.md#l1-proxy-withdraw-interface), and it will automatically unwrap tickets for a specified `receiver`.

Here is an example of the [withdraw](http://blockscout.dipdup.net/tx/0xac586320f475653b5fe8c4e0ce40f61147fd556069d0c268a989c98e8a31c3c1) operation.

#### Finalizing Tezos Withdrawal
To finalize the withdrawal process on the Tezos side, it is required to invoke the outbox message. An outbox message can be executed after it has been settled. To execute the message, the **commitment** hash and **proof** bytes need to be acquired. They are obtainable from the rollup node by **outboxLevel** and **outboxMsgId**.

> TODO: need to describe how to find `outboxLevel` and `outboxMsgId` using rollup RPC `global/block/cemented/outbox/{outbox_level}/messages`. Consider adding another command to iterate over last blocks to find messages?

After the withdrawal transaction is settled, users can retrieve the **commitment** and **proof**, which are necessary for the `execute_outbox_message` call. This involves making a call to the `global/block/head/helpers/proofs/outbox/{outbox_level}/messages` endpoint of the Rollup RPC Node. The `get_proof` script can be used to get this information:
```shell
poetry run get_proof --level 1181470 --index 0
```

Since the outbox message has settled on the L1 side, users can execute it by initiating the `execute_outbox_message` operation. Bellow a script `execute_outbox_message` used to finalize withdrawal for the test **FA1.2** token where acquired `--commitment` and `--proof` are provided:
```shell
poetry run execute_outbox_message \
    --commitment src13PirA1PzjLWRYJvNFJL5V6tfdbhzmAgML2UtQHuojjjFv6ARsf
    --proof 03000251dd09b9e7c635d0a23a9a02c6268edcf2a3e74a9980cd8ce568612f8dd6886951dd09b9e7c635d0a23a9a02c6268edcf2a3e74a9980cd8ce568612f8dd688690005820764757261626c65d09177f273e0b4b3646d59424754cbc1a5368b75a201a7fa133551e39afbc25b3903746167c00800000004536f6d650003c02411766c7a6adf7e0f2f3a1608fdde179275ff6881c5712387bd21d401d9365c820576616c7565810370766d8107627566666572738205696e707574820468656164c00100066c656e677468c00100066f75747075740004820132810a6c6173745f6c6576656cc0040012072b0133810f76616c69646974795f706572696f64c00400013b0082013181086f7574626f7865730200013b00c07dc3e23702625eb3ecd86216a989553e1c95c9611f209e54fcefbf598f96b849019e68014f18c0dda898697e4f913f5af0017d501c8dd825696ea12f41168fd98a1243d3d4b0ae0127a40113bf0109f2c0f8d9aa295d40a87361a32f534a539c3304d87286125baf97fad5692209f5e1a40104cec02e83ddeb15e1e93ccc0b9eeaa17453499b0acccefb56831e4b57f084467da05b01027101013800b1c00a9ab9a19d10248b3810f3be53af9fa0012280024e512fce2dc30653e85b94f20054002a0017c0e68c3b7ad7e6f130881c5da857a5992daf77fb911cf6a94fb669f9eeb6a11a23000ec0e48a085d60ed9f24c26a44d4d9825d545098165a8aec0a518059431f1a564ea30005c0ba795987ddd0ec6bbcaef394f12f322b7fe73ee5b5f53c0b95466fc9b9e165270004c0f37ede9ba69186bc32eb2d85541fe28de505097a3755fb0eed841ffe20ae0ace820731313230323030820468656164c00100066c656e677468c0010007313138313437300003810468656164c001008208636f6e74656e7473810130c0d3000000cf00000000ca07070a000000160000a79057282732a2736064001cf4b4c56b84ec31ee07070a000000160125cf30bfba37ed7907f524f7b4eaf304e03d09760007070707000005090a0000005f05020000005907040100000010636f6e74726163745f616464726573730a0000001c050a0000001601aca11e3f7734be9b46df1642a7d5f7d66c7bf6e8000704010000000a746f6b656e5f747970650a0000000b0501000000054641312e3200120125cf30bfba37ed7907f524f7b4eaf304e03d097600000000087769746864726177066c656e677468c00101c0ad7442a17d12b3355594da691f158d37a0d44a7eae4a901f02b78819014efa26c05bc495b3831636f3f356a681b5e81bc47c250151048452fd09ab24f5550d6334c00bece9f7a7ae300e23932bbc972eeebc35b64f82ddbf3ca35f3f911fe96189e0c0760bdf103b185a9ca7234e7a0b631c7e5a2c45d4a86aad483758c36db0017107c008796620943748d80efa68d459f16839f0b95891b566ec5ccbfa80e120e0f420c0ebe4e9a10f88ea5b510233f903f66ee80a8faa3c212a5bddf27421cc0deb7362c09cfb372f3f6c6f9659e15f9a8a9b3b3d2824a707c426d43eb8711e83bf2252990134810d6d6573736167655f6c696d6974c002a401047761736dd0d535afa926245d335484f18570628898b144af4686673c5dbd96fa2431025e4d0012071e0000000000ca07070a000000160000a79057282732a2736064001cf4b4c56b84ec31ee07070a000000160125cf30bfba37ed7907f524f7b4eaf304e03d09760007070707000005090a0000005f05020000005907040100000010636f6e74726163745f616464726573730a0000001c050a0000001601aca11e3f7734be9b46df1642a7d5f7d66c7bf6e8000704010000000a746f6b656e5f747970650a0000000b0501000000054641312e3200120125cf30bfba37ed7907f524f7b4eaf304e03d097600000000087769746864726177
```
Here is an example of the finished [withdrawal](https://oxfordnet.tzkt.io/oo9FJdy6byfy6HoTqpnzs68eLrpfwu1aouvnM8bv6HCbjrsXPF2/228622).