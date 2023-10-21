// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

/**
 * @dev Interface of the contract which can emit Withdraw event.
 */
interface IWithdrawEvent {
    /**
     * @dev Emitted when succesful withdraw is made.
     */
    // TODO: consider rename wrapper to ticketHolder?
    event Withdraw(
        bytes32 indexed withdrawalId,
        uint256 tokenHash,
        address wrapper,
        uint256 messageId,
        uint256 outboxLevel,
        address indexed sender,
        bytes indexed receiver,
        uint256 amount
    );
}
