// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {Test} from "forge-std/Test.sol";
import {ERC20Wrapper, IERC20Wrapper, hashToken} from "../src/ERC20Wrapper.sol";
import {BridgePrecompile} from "../src/BridgePrecompile.sol";

contract ERC20WrapperTest is Test, IERC20Wrapper {
    ERC20Wrapper public token;
    BridgePrecompile public bridge;
    address public alice = vm.addr(0x1);
    address public bob = vm.addr(0x2);
    uint256 public tokenHash;
    bytes20 public ticketer = bytes20("some ticketer");
    bytes20 public wrongTicketer = bytes20("some other ticketer");
    bytes32 public identifier = keccak256(abi.encodePacked("forged identifier"));
    bytes32 public wrongIdentifier =
        keccak256(abi.encodePacked("another forged identifier"));
    bytes32 receiver = "some receiver";

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
        bridge.deposit(address(token), alice, 100, tokenHash);
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
        uint256 wrongTokenHash = hashToken(wrongTicketer, identifier);
        bridge.deposit(address(token), alice, 100, wrongTokenHash);
    }

    function test_RevertWhen_IdentifierIsWrong() public {
        vm.expectRevert("ERC20Wrapper: wrong token hash");
        uint256 wrongTokenHash = hashToken(ticketer, wrongIdentifier);
        bridge.deposit(address(token), alice, 100, wrongTokenHash);
    }

    function test_WithdrawCallsBridgePrecompile() public {
        bridge.deposit(address(token), alice, 100, tokenHash);
        assertEq(token.balanceOf(alice), 100);
        bytes memory expectedData =
            abi.encodeCall(bridge.withdraw, (receiver, 50, tokenHash));
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
        // Only first topic is indexed, so we check it and check
        // that data the same (last argument is true))):
        vm.expectEmit(true, false, false, true);
        emit Deposit(bob, 100);
        bridge.deposit(address(token), bob, 100, tokenHash);
    }

    function test_ShouldEmitWithdrawEventOnWithdraw() public {
        bridge.deposit(address(token), bob, 100, tokenHash);
        vm.prank(bob);
        // Only first and second topics are indexed, so we check them
        // and check that data the same:
        vm.expectEmit(true, true, false, true);
        emit Withdraw(bob, receiver, 100);
        token.withdraw(receiver, 100);
    }
}
