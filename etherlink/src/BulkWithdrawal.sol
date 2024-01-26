// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

interface IWithdraw {
    function withdraw(
        address ticketOwner,
        bytes calldata receiver,
        uint256 amount,
        bytes22 ticketer,
        bytes calldata content
    ) external;
}

contract BulkWithdrawal {
    IWithdraw public kernel;

    constructor(address _kernel) {
        kernel = IWithdraw(_kernel);
    }

    function withdraw(
        address ticketOwner,
        bytes memory receiver,
        uint256 amount,
        bytes22 ticketer,
        bytes memory content
    ) public {
        kernel.withdraw(ticketOwner, receiver, amount, ticketer, content);
        kernel.withdraw(ticketOwner, receiver, amount, ticketer, content);
        kernel.withdraw(ticketOwner, receiver, amount, ticketer, content);
    }
}
