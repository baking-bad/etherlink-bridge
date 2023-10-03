// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {BaseTest} from "./Base.t.sol";
import {hashToken} from "../src/ERC20Wrapper.sol";
import {TokenData} from "../src/Kernel.sol";

contract KernelTest is BaseTest {
    function test_ShouldIncreaseTicketBalanceOfTokenIfDepositSucceed() public {
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        assertEq(kernel.getBalance(ticketer, identifier, address(token)), 100);
        assertEq(kernel.getBalance(ticketer, identifier, alice), 0);
    }

    // TODO: test_ShouldIncreaseTicketBalanceOfReceiverIfWrongTokenAddress

    function test_ShouldAddTokenDataIfDepositSucceed() public {
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        uint256 tokenHash = hashToken(ticketer, identifier);
        TokenData memory tokenData = kernel.getTokenData(tokenHash);
        assertEq(tokenData.ticketer, ticketer);
        assertEq(tokenData.identifier, identifier);
    }

    // TODO: test_ShouldDecreaseTicketBalanceOfTokenIfWithdrawSucceed
    // TODO: test_ShouldNotAllowToWithdrawMoreThanTicketBalance
}
