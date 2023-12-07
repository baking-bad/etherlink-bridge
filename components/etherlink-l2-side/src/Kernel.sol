// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {IWithdrawEvent} from "./IWithdrawEvent.sol";
import {IDepositEvent} from "./IDepositEvent.sol";
import {ERC20Wrapper, hashToken} from "./ERC20Wrapper.sol";

function hashTicketOwner(
    bytes22 ticketer,
    bytes memory identifier,
    address owner
) pure returns (bytes32) {
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
    uint256 private _rollupId;
    uint256 private _inboxLevel;
    uint256 private _outboxLevel;
    uint256 private _depositIdx;
    uint256 private _withdrawalIdx;

    mapping(bytes32 => uint256) private _tickets;

    /**
     * Increases `owner`'s tickets balance by `amount`.
     */
    function _increaseTicketsBalance(
        bytes22 ticketer,
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
        bytes22 ticketer,
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

    function getBalance(
        bytes22 ticketer,
        bytes memory identifier,
        address owner
    ) public view returns (uint256) {
        bytes32 ticket = hashTicketOwner(ticketer, identifier, owner);
        return _tickets[ticket];
    }

    /**
     * Emulates the deposit operation processed during inbox dispatch in Kernel.
     */
    function inboxDeposit(
        address wrapper,
        address receiver,
        uint256 amount,
        bytes22 ticketer,
        bytes memory identifier
    ) public {
        ERC20Wrapper token = ERC20Wrapper(wrapper);
        uint256 tokenHash = hashToken(ticketer, identifier);

        // NOTE: in the Kernel implementation if token.mint fails, then
        // ticket added to the receiver instead of the wrapper:
        _increaseTicketsBalance(ticketer, identifier, wrapper, amount);

        emit Deposit(
            tokenHash, wrapper, receiver, amount, _inboxLevel, _depositIdx
        );

        _depositIdx += 1;
        token.mint(receiver, amount, tokenHash);
    }

    function withdraw(
        address wrapper,
        bytes memory receiver,
        uint256 amount,
        bytes22 ticketer,
        bytes memory identifier
    ) public {
        ERC20Wrapper token = ERC20Wrapper(wrapper);
        address sender = msg.sender;
        uint256 tokenHash = hashToken(ticketer, identifier);
        _decreaseTicketsBalance(ticketer, identifier, wrapper, amount);

        emit Withdraw(
            tokenHash,
            sender,
            wrapper,
            receiver,
            amount,
            _outboxLevel,
            _withdrawalIdx
        );

        _withdrawalIdx += 1;
        token.burn(sender, amount, tokenHash);
        // NOTE: here the withdraw outbox message should be sent to L1
    }
}
