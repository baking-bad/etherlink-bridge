// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {BaseTest} from "./Base.t.sol";
import {ERC20Wrapper, hashToken} from "../src/ERC20Wrapper.sol";

contract ERC20WrapperTest is BaseTest {
    function test_BridgeCanMintToken() public {
        assertEq(token.balanceOf(alice), 0);
        kernel.inboxDeposit(address(token), alice, 100, ticketer, identifier);
        assertEq(token.balanceOf(alice), 100);
        assertEq(token.totalSupply(), 100);
    }

    function test_RevertWhen_AliceTriesMintToken() public {
        vm.prank(alice);
        vm.expectRevert(
            "ERC20Wrapper: only kernel allowed to mint / burn tokens"
        );
        token.mint(alice, 100, tokenHash);
    }

    function test_BridgeCanBurnToken() public {
        kernel.inboxDeposit(address(token), bob, 1, ticketer, identifier);
        assertEq(token.totalSupply(), 1);
        vm.prank(bob);
        kernel.withdraw(address(token), receiver, 1, tokenHash);
        assertEq(token.balanceOf(alice), 0);
        assertEq(token.totalSupply(), 0);
    }

    function test_RevertWhen_AliceTriesBurnToken() public {
        kernel.inboxDeposit(address(token), alice, 1, ticketer, identifier);
        vm.prank(alice);
        vm.expectRevert(
            "ERC20Wrapper: only kernel allowed to mint / burn tokens"
        );
        token.burn(alice, 1, tokenHash);
    }

    function test_RevertWhen_TicketerIsWrongOnMint() public {
        vm.expectRevert("ERC20Wrapper: wrong token hash");
        kernel.inboxDeposit(
            address(token), alice, 100, wrongTicketer, identifier
        );
    }

    function test_RevertWhen_IdentifierIsWrongOnMint() public {
        vm.expectRevert("ERC20Wrapper: wrong token hash");
        kernel.inboxDeposit(
            address(token), alice, 100, ticketer, wrongIdentifier
        );
    }

    function test_RevertWhen_TicketerIsWrongOnBurn() public {
        vm.expectRevert("ERC20Wrapper: wrong token hash");
        vm.prank(address(kernel));
        uint256 wrongTokenHash = hashToken(wrongTicketer, identifier);
        token.burn(alice, 1, wrongTokenHash);
    }

    function test_RevertWhen_IdentifierIsWrongOnBurn() public {
        vm.expectRevert("ERC20Wrapper: wrong token hash");
        vm.prank(address(kernel));
        uint256 wrongTokenHash = hashToken(ticketer, wrongIdentifier);
        token.burn(alice, 100, wrongTokenHash);
    }

    function test_ShouldReturnCorrectDecimals() public {
        assertEq(token.decimals(), 18);
        ERC20Wrapper anotherToken = new ERC20Wrapper(
            ticketer,
            identifier,
            address(kernel),
            "Another token",
            "ATKN",
            6
        );
        assertEq(anotherToken.decimals(), 6);
    }
}
