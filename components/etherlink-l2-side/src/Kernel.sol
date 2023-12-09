// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {IWithdrawEvent} from "./IWithdrawEvent.sol";
import {IDepositEvent} from "./IDepositEvent.sol";
import {ERC20Proxy, hashTicket} from "./ERC20Proxy.sol";

function hashTicketOwner(bytes22 ticketer, bytes memory content, address owner)
    pure
    returns (bytes32)
{
    return keccak256(abi.encodePacked(ticketer, content, owner));
}

/**
 * The Kernel is mock contract that used to represent the rollup kernel
 * on L2 side, which is resposible for bridging tokens between L1 and L2.
 * Kernel address is the one who should be allowed to mint new tokens in
 * ERC20Proxy contract.
 * The Kernel is responsible for maintainig the ledger of L2 tickets
 * and emiting `Deposit` and `Withdraw` events.
 */
contract Kernel is IWithdrawEvent, IDepositEvent {
    uint256 private _rollupId;
    uint256 private _inboxLevel;
    uint256 private _inboxMsgId;
    uint256 private _outboxLevel;
    uint256 private _outboxMsgId;

    mapping(bytes32 => uint256) private _tickets;

    /**
     * Increases `owner`'s tickets balance by `amount`.
     */
    function _increaseTicketsBalance(
        bytes22 ticketer,
        bytes memory content,
        address owner,
        uint256 amount
    ) internal {
        bytes32 ticketOwner = hashTicketOwner(ticketer, content, owner);
        _tickets[ticketOwner] += amount;
    }

    /**
     * Decreases `owner`'s tickets balance by `amount`.
     */
    function _decreaseTicketsBalance(
        bytes22 ticketer,
        bytes memory content,
        address owner,
        uint256 amount
    ) internal {
        bytes32 ticketOwner = hashTicketOwner(ticketer, content, owner);
        uint256 ticketBalance = _tickets[ticketOwner];
        if (ticketBalance < amount) {
            revert("Kernel: ticket balance is not enough");
        }
        _tickets[ticketOwner] -= amount;
    }

    function getBalance(bytes22 ticketer, bytes memory content, address owner)
        public
        view
        returns (uint256)
    {
        bytes32 ticket = hashTicketOwner(ticketer, content, owner);
        return _tickets[ticket];
    }

    /**
     * Emulates the deposit operation processed during inbox dispatch in Kernel.
     */
    function inboxDeposit(
        address ticketReceiver,
        address receiver,
        uint256 amount,
        bytes22 ticketer,
        bytes memory identifier
    ) public {
        ERC20Proxy proxyToken = ERC20Proxy(ticketReceiver);
        uint256 ticketHash = hashTicket(ticketer, identifier);

        // NOTE: in the Kernel implementation if proxyToken.deposit fails, then
        // ticket added to the receiver instead of the ticketReceiver:
        _increaseTicketsBalance(ticketer, identifier, ticketReceiver, amount);

        emit Deposit(
            ticketHash,
            ticketReceiver,
            receiver,
            amount,
            _inboxLevel,
            _inboxMsgId
        );

        _inboxMsgId += 1;
        proxyToken.deposit(receiver, amount, ticketHash);
    }

    function withdraw(
        address ticketOwner,
        bytes memory receiver,
        uint256 amount,
        bytes22 ticketer,
        bytes memory content
    ) public {
        ERC20Proxy proxyToken = ERC20Proxy(ticketOwner);
        address sender = msg.sender;
        uint256 ticketHash = hashTicket(ticketer, content);
        _decreaseTicketsBalance(ticketer, content, ticketOwner, amount);
        // NOTE: in the actual kernel, receiver type in event is bytes22
        //       - so to sync with the kernel, `bytes22 receiver` should be
        //       extracted from the `bytes memory receiver`.

        emit Withdraw(
            ticketHash,
            sender,
            ticketOwner,
            receiver,
            amount,
            _outboxLevel,
            _outboxMsgId
        );

        _outboxMsgId += 1;
        proxyToken.withdraw(sender, amount, ticketHash);
        // NOTE: here the withdraw outbox message should be sent to L1
    }
}
