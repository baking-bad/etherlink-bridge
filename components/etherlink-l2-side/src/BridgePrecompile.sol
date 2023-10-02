// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20Wrapper} from "./ERC20Wrapper.sol";
import {IWithdrawEvent} from "./IWithdrawEvent.sol";
import {IDepositEvent} from "./IDepositEvent.sol";

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

    // TODO: methods to set messageId & outboxLevel?

    constructor() {
        this;
        _outboxMessageId = 0;
        _outboxLevel = 0;
    }

    function deposit(
        bytes32 depositId,
        address wrapper,
        address receiver,
        uint256 amount,
        uint256 tokenHash
    ) public {
        // TODO: add require that will allow only kernel to emit events
        emit Deposit(depositId, tokenHash, wrapper, receiver, amount);
    }

    function withdraw(
        address from,
        bytes20 receiver,
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
        // TODO: call Kernel to update the ledger of L2 tickets
        // NOTE: in the final implementation no real call should be made
        //       the BridgePrecompile should be allowed to modify the ledger
        //       directly.
        _outboxMessageId += 1;
    }
}
