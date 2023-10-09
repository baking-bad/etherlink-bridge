// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {BaseTest} from "./Base.t.sol";
import {ERC20Wrapper} from "../src/ERC20Wrapper.sol";

contract ERC20WrapperTest is BaseTest {
    function test_BridgeCanMintToken() public {
        assertEq(token.balanceOf(alice), 0);
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        assertEq(token.balanceOf(alice), 100);
        assertEq(token.totalSupply(), 100);
    }

    function test_RevertWhen_AliceTriesMintToken() public {
        vm.prank(alice);
        vm.expectRevert("ERC20Wrapper: only kernel allowed to mint tokens");
        token.deposit(alice, 100, tokenHash);
    }

    function test_RevertWhen_TicketerIsWrong() public {
        vm.expectRevert("ERC20Wrapper: wrong token hash");
        kernel.inboxDeposit(
            address(token), alice, 100, wrongTicketer, identifier
        );
    }

    function test_RevertWhen_IdentifierIsWrong() public {
        vm.expectRevert("ERC20Wrapper: wrong token hash");
        kernel.inboxDeposit(
            address(token), alice, 100, ticketer, wrongIdentifier
        );
    }

    function test_WithdrawCallsBridgePrecompile() public {
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        assertEq(token.balanceOf(alice), 100);
        bytes memory expectedData =
            abi.encodeCall(bridge.withdraw, (alice, receiver, 50, tokenHash));
        vm.expectCall(address(bridge), expectedData);
        vm.prank(alice);
        token.withdraw(receiver, 50);
        assertEq(token.balanceOf(alice), 50);
    }

    function test_ShouldReturnCorrectDecimals() public {
        assertEq(token.decimals(), 18);
        ERC20Wrapper anotherToken = new ERC20Wrapper(
            ticketer,
            identifier,
            address(kernel),
            address(bridge),
            "Another token",
            "ATKN",
            6
        );

        assertEq(anotherToken.decimals(), 6);
    }
}
