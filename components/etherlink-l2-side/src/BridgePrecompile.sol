// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {IWithdrawEvent} from "./IWithdrawEvent.sol";
import {IDepositEvent} from "./IDepositEvent.sol";
import {Kernel} from "./Kernel.sol";

/**
 * BridgePrecompile is a special contract which is used to represent
 * the bridge precompile contract logic on L2 side. It is used to
 * emit events.
 */
contract BridgePrecompile is IWithdrawEvent, IDepositEvent {
    // NOTE: outboxMessageId and outboxLevel are parameters of the Kernel,
    //       however BridgePrecompile should have access to them.
    // TODO: is uint256 enough for messageId?
    uint256 private _outboxMessageId;
    uint256 private _outboxLevel;
    address private _kernel;

    // TODO: methods to set messageId & outboxLevel?

    constructor(address kernel) {
        this;
        _outboxMessageId = 0;
        _outboxLevel = 0;
        _kernel = kernel;
    }

    /**
     * Checks if the sender is the kernel address.
     */
    function _requireSenderIsKernel() internal view {
        require(
            _kernel == msg.sender,
            "BridgePrecompile: only kernel allowed to deposit and withdraw tokens"
        );
    }

    function deposit(
        bytes32 depositId,
        address wrapper,
        address receiver,
        uint256 amount,
        uint256 tokenHash
    ) public {
        _requireSenderIsKernel();
        emit Deposit(depositId, tokenHash, wrapper, receiver, amount);
    }

    function withdraw(
        address wrapper,
        address from,
        bytes memory receiver,
        uint256 amount,
        uint256 tokenHash
    ) public {
        _requireSenderIsKernel();
        bytes32 withdrawalId =
            keccak256(abi.encodePacked(_outboxMessageId, _outboxLevel));
        emit Withdraw(
            withdrawalId,
            tokenHash,
            wrapper,
            _outboxMessageId,
            _outboxLevel,
            from,
            receiver,
            amount
        );
        _outboxMessageId += 1;
    }
}
