// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

/**
 * @dev Interface of the contract which can emit Withdraw event.
 */
interface IWithdrawEvent {
    /**
     * @dev Emitted when succesful withdraw is made.
     */
    event Withdraw(
        uint256 indexed tokenHash,
        address sender,
        address tiketOwner,
        bytes receiver,
        uint256 amount,
        uint256 outboxLevel,
        uint256 outboxMsgId
    );
}
