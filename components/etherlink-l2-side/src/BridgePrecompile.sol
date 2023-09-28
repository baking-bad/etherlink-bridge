// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20Wrapper} from "./ERC20Wrapper.sol";
import {IWithdraw} from "./IWithdraw.sol";

contract BridgePrecompile is IWithdraw {
    // TODO: is uint256 enough for messageId?
    uint256 private outboxMessageId;
    uint256 private outboxLevel;

    // TODO: methods to set messageId & outboxLevel?

    constructor() {
        this;
        outboxMessageId = 0;
        outboxLevel = 0;
    }

    function deposit(
        bytes32 depositId,
        address wrapper,
        address to,
        uint256 amount,
        uint256 tokenHash
    ) public {
        ERC20Wrapper token = ERC20Wrapper(wrapper);
        token.deposit(depositId, to, amount, tokenHash);
    }

    function withdraw(
        address from,
        bytes20 receiver,
        uint256 amount,
        uint256 tokenHash
    ) public {
        bytes32 withdrawalId =
            keccak256(abi.encodePacked(outboxMessageId, outboxLevel));
        emit Withdraw(
            withdrawalId, outboxMessageId, outboxLevel, from, receiver, amount
        );
    }
}
