// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {BaseTest} from "./Base.t.sol";

contract KernelTest is BaseTest {
    function test_ShouldIncreaseTicketBalanceOfTokenIfDepositSucceed() public {
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 100);
        assertEq(kernel.getBalance(ticketer, identifier, alice), 0);
    }

    // TODO: test_ShouldIncreaseTicketBalanceOfReceiverIfWrongTokenAddress
    // TODO: test_ShouldAddTokenDataIfDepositSucceed
    // TODO: test_ShouldDecreaseTicketBalanceOfTokenIfWithdrawSucceed
    // TODO: test_ShouldNotAllowToWithdrawMoreThanTicketBalance
}
