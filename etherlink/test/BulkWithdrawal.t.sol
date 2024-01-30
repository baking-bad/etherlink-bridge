// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {BaseTest} from "./Base.t.sol";
import {BulkWithdrawal} from "../src/BulkWithdrawal.sol";
import {ERC20Proxy, hashTicket} from "../src/ERC20Proxy.sol";

contract BulkWithdrawalTest is BaseTest {
    BulkWithdrawal public bulkWithdrawal;

    function test_WithdrawalFromSmartContractSucceed() public {
        bulkWithdrawal = new BulkWithdrawal(address(kernel));
        kernel.inboxDeposit(
            address(token), address(bulkWithdrawal), 100, ticketer, content
        );
        assertEq(token.totalSupply(), 100);

        bytes memory expectedData = abi.encodeCall(
            kernel.withdraw, (address(token), receiver, 12, ticketer, content)
        );
        vm.expectCall(address(kernel), expectedData);
        vm.prank(bob);
        // bulk withdrawal makes 3 withdrawals in one transaction:
        bulkWithdrawal.withdraw(address(token), receiver, 12, ticketer, content);
        assertEq(token.balanceOf(address(bulkWithdrawal)), 100 - 12 * 3);
        assertEq(token.totalSupply(), 100 - 12 * 3);
    }
}
