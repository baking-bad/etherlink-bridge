// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {Test} from "forge-std/Test.sol";
import {ERC20Wrapper, hashToken} from "../src/ERC20Wrapper.sol";
import {BridgePrecompile} from "../src/BridgePrecompile.sol";
import {IDepositEvent} from "../src/IDepositEvent.sol";
import {IWithdrawEvent} from "../src/IWithdrawEvent.sol";

contract ERC20WrapperTest is Test, IDepositEvent, IWithdrawEvent {
    ERC20Wrapper public token;
    BridgePrecompile public bridge;
    address public alice = vm.addr(0x1);
    address public bob = vm.addr(0x2);
    uint256 public tokenHash;
    bytes20 public ticketer = bytes20("some ticketer");
    bytes20 public wrongTicketer = bytes20("some other ticketer");
    bytes public identifier = abi.encodePacked("forged identifier");
    bytes public wrongIdentifier = abi.encodePacked("another forged identifier");
    bytes20 public receiver = bytes20("some receiver");
    bytes32 public depositId = keccak256(abi.encodePacked("some deposit id"));

    function setUp() public {
        vm.label(alice, "Alice");
        vm.label(bob, "Bob");
        bridge = new BridgePrecompile();
        token = new ERC20Wrapper(
            ticketer,
            identifier,
            address(bridge),
            "Token",
            "TKN",
            18
        );
        tokenHash = hashToken(ticketer, identifier);
    }

    function test_BridgeCanMintToken() public {
        assertEq(token.balanceOf(alice), 0);
        bridge.deposit(depositId, address(token), alice, 100, tokenHash);
        assertEq(token.balanceOf(alice), 100);
        assertEq(token.totalSupply(), 100);
    }

    function test_RevertWhen_AliceTriesMintToken() public {
        vm.prank(alice);
        vm.expectRevert("ERC20Wrapper: only kernel allowed to mint tokens");
        token.deposit(depositId, alice, 100, tokenHash);
    }

    function test_RevertWhen_TicketerIsWrong() public {
        vm.expectRevert("ERC20Wrapper: wrong token hash");
        uint256 wrongTokenHash = hashToken(wrongTicketer, identifier);
        bridge.deposit(depositId, address(token), alice, 100, wrongTokenHash);
    }

    function test_RevertWhen_IdentifierIsWrong() public {
        vm.expectRevert("ERC20Wrapper: wrong token hash");
        uint256 wrongTokenHash = hashToken(ticketer, wrongIdentifier);
        bridge.deposit(depositId, address(token), alice, 100, wrongTokenHash);
    }

    function test_WithdrawCallsBridgePrecompile() public {
        bridge.deposit(depositId, address(token), alice, 100, tokenHash);
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
            address(bridge),
            "Another token",
            "ATKN",
            6
        );

        assertEq(anotherToken.decimals(), 6);
    }

    function test_ShouldEmitDepositEventOnDeposit() public {
        // All topics are indexed, so we check all of them and
        // that data the same (last argument is true):
        vm.expectEmit(true, true, true, true);
        emit Deposit(depositId, bob, 100);
        bridge.deposit(depositId, address(token), bob, 100, tokenHash);
    }

    function test_ShouldEmitWithdrawEventOnWithdraw() public {
        bridge.deposit(depositId, address(token), bob, 100, tokenHash);
        vm.prank(bob);
        // All topics are indexed, so we check them all
        // and check that data the same:
        vm.expectEmit(true, true, true, true);
        uint256 messageId = 0;
        uint256 outboxLevel = 0;
        bytes32 withdrawalId =
            keccak256(abi.encodePacked(messageId, outboxLevel));
        emit Withdraw(withdrawalId, messageId, outboxLevel, bob, receiver, 100);
        token.withdraw(receiver, 100);
    }
}
