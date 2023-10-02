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
        bytes32 indexed depositId,
        uint256 indexed tokenHash,
        address token,
        address indexed receiver,
        uint256 amount
    );
}
