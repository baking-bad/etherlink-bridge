// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import {Test} from "forge-std/Test.sol";
import {hashTicket} from "../src/ERC20Proxy.sol";
import "forge-std/console.sol";

contract HashTicketTest is Test {
    function test_ShouldNotHaveSameHash() public {
        bytes22 ticketer = hex"012183acb41c745886a3df8a47e21b14703a9794d700";
        bytes memory contentA =
            hex"000000000000000000000000000000000000000000000000000000000000000001";
        bytes memory contentB =
            hex"000000000000000000000000000000000000000000000000000000000000000002";

        console.logBytes(contentA);
        console.logBytes(contentB);

        uint256 ticketHashA = hashTicket(ticketer, contentA);
        uint256 ticketHashB = hashTicket(ticketer, contentB);
        console.logUint(ticketHashA);
        console.logUint(ticketHashB);
        assertNotEq(ticketHashA, ticketHashB);
    }
}
