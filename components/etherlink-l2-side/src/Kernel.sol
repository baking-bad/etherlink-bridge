// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {IWithdrawEvent} from "./IWithdrawEvent.sol";
import {IDepositEvent} from "./IDepositEvent.sol";
import {ERC20Wrapper, hashToken} from "./ERC20Wrapper.sol";

function hashTicketOwner(
    bytes20 ticketer,
    bytes memory identifier,
    address owner
) pure returns (bytes32) {
    // TODO: consider replacing encodePacked with encode:
    //       looks like type collision is impossible here, but
    //       maybe it is better to use encode? [2]
    return keccak256(abi.encodePacked(ticketer, identifier, owner));
}

/**
 * The Kernel is mock contract that used to represent the rollup kernel
 * on L2 side, which is resposible for bridging tokens between L1 and L2.
 * Kernel address is the one who should be allowed to mint new tokens in
 * ERC20Wrapper contract.
 * The Kernel is responsible for maintainig the ledger of L2 tickets
 * and emiting `Deposit` and `Withdraw` events.
 */
contract Kernel is IWithdrawEvent, IDepositEvent {
    uint256 private _inboxLevel;
    uint256 private _inboxMessageId;
    uint256 private _outboxMessageId;
    uint256 private _outboxLevel;

    mapping(bytes32 => uint256) private _tickets;

    /**
     * Increases `owner`'s tickets balance by `amount`.
     */
    function _increaseTicketsBalance(
        bytes20 ticketer,
        bytes memory identifier,
        address owner,
        uint256 amount
    ) internal {
        bytes32 ticketOwner = hashTicketOwner(ticketer, identifier, owner);
        _tickets[ticketOwner] += amount;
    }

    /**
     * Decreases `owner`'s tickets balance by `amount`.
     */
    function _decreaseTicketsBalance(
        bytes20 ticketer,
        bytes memory identifier,
        address owner,
        uint256 amount
    ) internal {
        bytes32 ticketOwner = hashTicketOwner(ticketer, identifier, owner);
        uint256 ticketBalance = _tickets[ticketOwner];
        if (ticketBalance < amount) {
            revert("Kernel: ticket balance is not enough");
        }
        _tickets[ticketOwner] -= amount;
    }

    /**
     * Emulates the deposit operation processed during inbox dispatch in Kernel.
     */
    function inboxDeposit(
        address wrapper,
        address receiver,
        uint256 amount,
        bytes20 ticketer,
        bytes memory identifier
    ) public {
        ERC20Wrapper token = ERC20Wrapper(wrapper);

        uint256 tokenHash = hashToken(ticketer, identifier);
        // TODO: consider passing depositId in params instead of constructing
        // it here, because depositId might become hashed L1 operation contents
        bytes32 depositId =
            keccak256(abi.encodePacked(_inboxMessageId, _inboxLevel));
        _inboxMessageId += 1;

        // NOTE: in the Kernel implementation if token.mint fails, then
        // ticket added to the receiver instead of the wrapper:
        _increaseTicketsBalance(ticketer, identifier, wrapper, amount);
        emit Deposit(depositId, tokenHash, wrapper, receiver, amount);
        token.mint(receiver, amount, tokenHash);
    }

    function getBalance(
        bytes20 ticketer,
        bytes memory identifier,
        address owner
    ) public view returns (uint256) {
        bytes32 ticket = hashTicketOwner(ticketer, identifier, owner);
        return _tickets[ticket];
    }

    function withdraw(
        address wrapper,
        bytes memory receiver,
        uint256 amount,
        bytes20 ticketer,
        bytes memory identifier
    ) public {
        ERC20Wrapper token = ERC20Wrapper(wrapper);

        address from = msg.sender;
        uint256 tokenHash = hashToken(ticketer, identifier);
        _decreaseTicketsBalance(ticketer, identifier, wrapper, amount);
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
        token.burn(from, amount, tokenHash);
        // NOTE: here the withdraw outbox message should be sent to L1
    }
}
