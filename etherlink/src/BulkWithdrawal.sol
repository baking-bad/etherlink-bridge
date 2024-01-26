// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {BatchCallHelper} from "./BatchCallHelper.sol";

contract BulkWithdrawal is BatchCallHelper {
    address public faPrecompile;
    address public xtzPrecompile;
    uint256 public callsCount;

    constructor(
        address faPrecompile_,
        address xtzPrecompile_,
        uint256 callsCount_
    ) {
        faPrecompile = faPrecompile_;
        xtzPrecompile = xtzPrecompile_;
        callsCount = callsCount_;
    }

    // TODO: add a way to set the callsCount
    // TODO: add a way to set the precompile addresses

    function withdraw(
        address ticketOwner,
        bytes memory routingInfo,
        uint256 amount,
        bytes22 ticketer,
        bytes memory content
    ) public {
        // TODO: note that contract should have tokens on balance

        bytes memory callData = abi.encodeWithSignature(
            "withdraw(address,bytes,uint256,bytes22,bytes)",
            ticketOwner,
            routingInfo,
            amount,
            ticketer,
            content
        );
        _makeCallMultipleTimes(faPrecompile, callData, 0, callsCount);
    }

    function withdraw_base58(string memory target) public payable {
        // TODO: note that contract should have L2-xtz on balance and
        // it would copy the current added value to the target contract
        // multiple times

        bytes memory callData =
            abi.encodeWithSignature("withdraw_base58(string)", target);
        _makeCallMultipleTimes(xtzPrecompile, callData, msg.value, callsCount);
    }

    // TODO: explain that this function used to receive xtz
    receive() external payable {}
}
