// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {BatchCallHelper} from "./BatchCallHelper.sol";

contract TokenProxyTester is BatchCallHelper {
    uint256 private _lock;
    address public withdrawalPrecompile;
    bytes public routingInfo;
    uint256 public amount;
    bytes22 public ticketer;
    bytes public content;
    uint256 public callsCount;

    /**
     * @notice Constructs the TokenProxyTester.
     * @param withdrawalPrecompile_ The address of the withdrawal precompile contract.
     * @param routingInfo_ The routing information for the withdrawal.
     * @param amount_ The amount of tokens to withdraw.
     * @param ticketer_ The address of the ticketer.
     * @param content_ The content of the ticket.
     * @param callsCount_ The number of calls to make during deposit and withdrawal.
     */
    constructor(
        address withdrawalPrecompile_,
        bytes memory routingInfo_,
        uint256 amount_,
        bytes22 ticketer_,
        bytes memory content_,
        uint256 callsCount_
    ) {
        _lock = 0;
        setParameters(
            withdrawalPrecompile_,
            routingInfo_,
            amount_,
            ticketer_,
            content_,
            callsCount_
        );
    }

    /**
     * @notice Sets the parameters for the TokenProxyTester.
     * @param withdrawalPrecompile_ The address of the withdrawal precompile contract.
     * @param routingInfo_ The routing information for the withdrawal.
     * @param amount_ The amount of tokens to withdraw.
     * @param ticketer_ The address of the ticketer.
     * @param content_ The content of the ticket.
     * @param callsCount_ The number of calls to make during deposit and withdrawal.
     */
    function setParameters(
        address withdrawalPrecompile_,
        bytes memory routingInfo_,
        uint256 amount_,
        bytes22 ticketer_,
        bytes memory content_,
        uint256 callsCount_
    ) public {
        withdrawalPrecompile = withdrawalPrecompile_;
        routingInfo = routingInfo_;
        amount = amount_;
        ticketer = ticketer_;
        content = content_;
        callsCount = callsCount_;
    }

    function _makeCallsToWithdrawlPrecomple() internal {
        bytes memory data = abi.encodeWithSignature(
            "withdraw(address,bytes,uint256,bytes22,bytes)",
            address(this),
            routingInfo,
            amount,
            ticketer,
            content
        );
        _makeCallMultipleTimes(withdrawalPrecompile, data, 0, callsCount);
    }

    /**
     * Ignores reentrant calls.
     */
    modifier ignoreReentrant() {
        if (_lock == 0) {
            _lock = 1;
            _;
            _lock = 0;
        } else {
            return;
        }
    }

    /**
     * @notice Mocks the deposit function.
     */
    function deposit(address, uint256, uint256) public {
        _makeCallsToWithdrawlPrecomple();
    }

    /**
     * @notice Mocks the withdraw function, ignores reentrancy.
     */
    function withdraw(address, uint256, uint256) public ignoreReentrant {
        _makeCallsToWithdrawlPrecomple();
    }
}
