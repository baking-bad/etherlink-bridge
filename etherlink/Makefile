# Load environment variables from .env file:
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

RPC_URL := http://etherlink.piltover.baking-bad.org
TICKETER_ADDRESS_BYTES := 0134b965e6525309eb010bd5fb326e0a2d1f6d8c4400
TICKETER_CONTENT_BYTES := 070700000306
PROXY_ERC20_ADDRESS := 0x7234dB1E040eD8d9752ef34a843909Bc05a691a1
KERNEL_ADDRESS := 0x0000000000000000000000000000000000000000
WITHDRAW_PRECOMPILE_ADDRESS := 0x0000000000000000000000000000000000000040
L1_RECEIVER_ADDRESS := 0000ec9164b511e02a5ef797a01746c7a4b37fd9053c

fund_accounts:
	cast send $(L2_ALICE_PUBLIC_KEY) --value 1ether --private-key $(L2_MANAGER_PRIVATE_KEY) --rpc-url $(RPC_URL) --legacy
	cast send $(L2_BORIS_PUBLIC_KEY) --value 1ether --private-key $(L2_MANAGER_PRIVATE_KEY) --rpc-url $(RPC_URL) --legacy

deploy_proxy_erc20:
	forge create --legacy --rpc-url $(RPC_URL) --private-key $(L2_ALICE_PRIVATE_KEY) src/ERC20Proxy.sol:ERC20Proxy --constructor-args $(TICKETER_ADDRESS_BYTES) $(TICKETER_CONTENT_BYTES) $(KERNEL_ADDRESS) "Test Token" "TST" 0 --gas-limit 200000

play_withdraw:
	cast send $(PROXY_ERC20_ADDRESS) "transfer(address,uint256)" $(L2_BORIS_PUBLIC_KEY) 42 --rpc-url $(RPC_URL) --private-key $(L2_ALICE_PRIVATE_KEY) --legacy --gas-limit 300000
	sleep 10
	cast send $(WITHDRAW_PRECOMPILE_ADDRESS) "withdraw(address,bytes,uint256,bytes22,bytes)" $(PROXY_ERC20_ADDRESS) $(L1_RECEIVER_ADDRESS) 17 $(TICKETER_ADDRESS_BYTES) $(TICKETER_CONTENT_BYTES) --rpc-url $(RPC_URL) --private-key $(L2_BORIS_PRIVATE_KEY) --legacy --gas-limit 300000

