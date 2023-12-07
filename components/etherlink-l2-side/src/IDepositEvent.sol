// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

/**
 * @dev Interface of the contract which can emit Deposit event.
 */
interface IDepositEvent {
    /**
     * @dev Emitted when succesful deposit is made.
     */
    event Deposit(
        uint256 indexed tokenHash,
        address ticketOwner,
        address receiver,
        uint256 amount,
        uint256 inboxLevel,
        uint256 inboxMsgId
    );
}
