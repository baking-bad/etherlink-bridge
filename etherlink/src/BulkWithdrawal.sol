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
    address public kernel_address;

    event LogEvent(uint256 num);

    constructor(address _kernel_address) {
        kernel_address = _kernel_address;
    }

    function withdraw(
        address ticketOwner,
        bytes memory routing_info,
        uint256 amount,
        bytes22 ticketer,
        bytes memory content
    ) public {
        IWithdraw kernel = IWithdraw(kernel_address);
        emit LogEvent(0);
        kernel.withdraw(ticketOwner, routing_info, amount, ticketer, content);
        emit LogEvent(1);
    }
}
