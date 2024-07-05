### Bridge configuration
To configure the bridge for a new token (i.e., to list a new token pair), users need to engage with the **Ticket Transport Layer**. This critical component of the bridge facilitates the transfer of tickets between Tezos and Etherlink.

![permissionless ticket transfer short illustration](permissionless-ticket-transfer.png)

The **FA2** and **FA1.2** standard Tezos tokens are not inherently ticket-native. Therefore, to bridge these tokens, users must initially convert them to tickets. To do this they first need to deploy a **Ticketer** contract on the Tezos side. This contract will be associated with the specific Tezos token and provide entrypoint to wrap them into tickets. This contract is unnecessary for the forthcoming tokens that are ticket-native, such as those following **FA2.1** standard.

NOTE: Upgrades to the Ticketer contract are highly unwanted because this will lead to liquidity fragmentation. Ideally, it should be deployed once and remain unchanged indefinitely.

Once it's determined what **Ticketer** will represent the token, users can deploy an **ERC20Proxy** – an ERC20 token integrated with bridge deposit and withdrawal interfaces. The Ticketer address and ticket content are provided to the ERC20Proxy constructor during origination to bind the L2 token to the L1 ticket. It is also required to provide rollup kernel address to the ERC20 proxy which will be allowed to mint and burn tokens which is the `0x00` address.

Additionally, deploying a **TokenBridgeHelper** on the Tezos side is required, targeting the specific **Token** and **Ticketer** pair on the L1 side and **ERC20Proxy** address on the L2 side. This deployment is crucial since wallets currently do not support the **transfer_ticket** operation. The **TokenBridgeHelper** streamlines the process by wrapping tokens into tickets and enabling their transfer to the rollup in a single transaction. Note, however, that this type of contract may become obsolete in the future when (1) wallets begin supporting the **transfer_ticket** operation and (2) Tezos undergoes a protocol upgrade that permits implicit addresses to transfer tickets with arbitrary data.

#### Deploying a Token
For demonstration purposes, users can deploy a test token intended for bridging. The bridge has been tested with two types of tokens available in the repository:
- The **FA1.2** standard **Ctez** token.
- The **FA2** standard **fxhash** token.

To deploy a test version of a token and allocate the total supply to the token's originator, the `deploy_token` command can be used. It is possible to configure `--token-type`, `--token-id`, and `--total-supply` providing these params to the command. The following example demonstrates how to deploy an **FA1.2** token type using default parameters:
```shell
poetry run deploy_token --token-type FA1.2 --total-supply 1000
```
Here is an example of the deployed [token](https://oxfordnet.tzkt.io/KT1QKYoSpV5BLKg8xoexG25yZwA1sjVrrymU/operations/).

#### Deploying a Ticketer
The `deploy_ticketer` command can be used to deploy a ticketer configured for a specific token. It requires the `--token-address`, `--token-type`, and `--token-id` parameters to be provided. Below is an example that demonstrates how to deploy a ticketer for the **FA1.2** token previously deployed on Oxfordnet:
```shell
poetry run deploy_ticketer --token-address KT1QKYoSpV5BLKg8xoexG25yZwA1sjVrrymU --token-type FA1.2
```
Here is an example of the deployed [ticketer](https://oxfordnet.tzkt.io/KT1C2gmhvA1FrscWe8KbrHf8dWG9XJETR127/metadata).

After the Ticketer contract is deployed, users can obtain the parameters required for the **ERC20Proxy** origination, **ticketer-address_bytes** and **content_bytes**. To do this users can execute `get_ticketer_params` command:
```shell
poetry run get_ticketer_params --ticketer KT1C2gmhvA1FrscWe8KbrHf8dWG9XJETR127
```

For example, the ticketer deployed in the previous step has the following parameters:
```
address_bytes: 0125cf30bfba37ed7907f524f7b4eaf304e03d097600
content_bytes: 0707000005090a0000005f05020000005907040100000010636f6e74726163745f616464726573730a0000001c050a0000001601aca11e3f7734be9b46df1642a7d5f7d66c7bf6e8000704010000000a746f6b656e5f747970650a0000000b0501000000054641312e32
```

#### Deploying ERC20Proxy
Then, to deploy a token contract on the Etherlink side, the `deploy_erc20` command can be used. This script requires the `--ticketer-address-bytes` and `--ticketer-content-bytes`, as well as `--token-name`, `--token-symbol`, and `--decimals` to be provided for the L2 token contract configuration. Below is an example that originates ERC20 contract connected to the ticketer previously deployed:
```shell
poetry run deploy_erc20 --ticketer-address-bytes 0125cf30bfba37ed7907f524f7b4eaf304e03d097600 --ticket-content-bytes 0707000005090a0000005f05020000005907040100000010636f6e74726163745f616464726573730a0000001c050a0000001601aca11e3f7734be9b46df1642a7d5f7d66c7bf6e8000704010000000a746f6b656e5f747970650a0000000b0501000000054641312e32 --token-name "FA1.2 Test Token" --token-symbol "FA1.2" --decimals 0
```
Here is an example of the deployed [token](http://blockscout.dipdup.net/address/0x03E39FF2b379FBcd9284Ab457113D82fF4daBBF4).

#### Deploying a Token Bridge Helper
Finally, to allow the interaction of Tezos wallets with tickets, users need to deploy a Token Bridge Helper. During origination, Token Bridge Helper linked to the Token, Ticketer and ERC20Proxy. To originate Token Bridge Helper user should run the `deploy_token_bridge_helper` command, which requires the `--ticketer-address` and `--proxy-address` (the address of the L2 token) parameters to be provided. The Ticketer's storage will be parsed to retrieve information about the token. Below is an example that illustrates deploying a token bridge helper for the previously deployed ticketer and proxy:
```shell
poetry run deploy_token_bridge_helper --ticketer-address KT1C2gmhvA1FrscWe8KbrHf8dWG9XJETR127 --proxy-address 0x03E39FF2b379FBcd9284Ab457113D82fF4daBBF4
```
Here is an example of the deployed [helper](https://oxfordnet.tzkt.io/KT1RWw9NyPDZm9jeiEA1hXMd4PgGQVPHYrzj/metadata).
