// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20Wrapper} from "./ERC20Wrapper.sol";
import {IWithdrawEvent} from "./IWithdrawEvent.sol";
import {IDepositEvent} from "./IDepositEvent.sol";
import {Kernel} from "./Kernel.sol";

/**
 * BridgePrecompile is a special contract which is used to represent
 * the bridge precompile contract logic on L2 side. It is used to
 * emit events and initiate withdrawals from ERC20 tokens.
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

    function deposit(
        bytes32 depositId,
        address wrapper,
        address receiver,
        uint256 amount,
        uint256 tokenHash
    ) public {
        require(
            _kernel == msg.sender,
            "BridgePrecompile: only kernel allowed to deposit tokens"
        );
        emit Deposit(depositId, tokenHash, wrapper, receiver, amount);
    }

    function withdraw(
        address from,
        bytes memory receiver,
        uint256 amount,
        uint256 tokenHash
    ) public {
        bytes32 withdrawalId =
            keccak256(abi.encodePacked(_outboxMessageId, _outboxLevel));
        address wrapper = msg.sender;
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
        Kernel kernel = Kernel(_kernel);
        // NOTE: in the final implementation no real call to Kernel should be
        //       made, the BridgePrecompile should be allowed to modify the
        //       ledger directly without calling Kernel
        kernel.finalizeWithdraw(tokenHash, wrapper, amount);
    }
}
