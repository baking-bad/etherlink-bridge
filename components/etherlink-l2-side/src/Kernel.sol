// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20Wrapper, hashToken} from "./ERC20Wrapper.sol";
import {BridgePrecompile} from "./BridgePrecompile.sol";

/**
 * The Kernel is mock contract that used to represent the rollup kernel
 * on L2 side, which is resposible for bridging tokens between L1 and L2.
 * Kernel address is the one who should be allowed to mint new tokens in
 * ERC20Wrapper contract.
 * The Kernel is responsible for maintainig the ledger of L2 tickets
 */
contract Kernel {
    address private _bridge;
    uint256 private _inboxLevel;
    uint256 private _inboxMessageId;

    constructor(address bridge) {
        _bridge = bridge;
        _inboxLevel = 0;
    }

    function inboxDeposit(
        address wrapper,
        address receiver,
        uint256 amount,
        bytes20 ticketer,
        bytes memory identifier
    ) public {
        // TODO: save tokenHash to (ticketer, identifier) mapping
        // TODO: update ledger of L2 tickets

        ERC20Wrapper token = ERC20Wrapper(wrapper);
        BridgePrecompile bridge = BridgePrecompile(_bridge);

        uint256 tokenHash = hashToken(ticketer, identifier);
        bytes32 depositId =
            keccak256(abi.encodePacked(_inboxMessageId, _inboxLevel));

        _inboxMessageId += 1;

        bridge.deposit(depositId, wrapper, receiver, amount, tokenHash);
        token.deposit(receiver, amount, tokenHash);
    }

    // TODO: implement finalizeWithdraw which should be called by the
    //       BridgePrecompile contract and which should update the L2
    //       tickets ledger.
}
