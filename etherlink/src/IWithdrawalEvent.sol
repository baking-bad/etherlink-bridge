// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

/**
 * @dev Interface of the contract which can emit Withdrawal event.
 */
interface IWithdrawalEvent {
    /**
     * @dev Emitted when succesful withdrawal is made.
     */
    event Withdrawal(
        uint256 indexed ticketHash,
        address sender,
        address tiketOwner,
        bytes22 receiver,
        uint256 amount,
        uint256 outboxLevel,
        uint256 outboxMsgId
    );
}
