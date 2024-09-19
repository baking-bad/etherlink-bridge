// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

contract OutboxEnumerator {
    address public xtzPrecompile;
    uint256 public callsCount;

    constructor(address xtzPrecompile_, uint256 callsCount_) {
        xtzPrecompile = xtzPrecompile_;
        callsCount = callsCount_;
    }

    // TODO: describe that this contract make multiple calls to the
    // withdrawal precompile with different amounts
    function withdraw_base58(string memory target) public payable {
        bytes memory data =
            abi.encodeWithSignature("withdraw_base58(string)", target);
        uint256 counter = 1;
        while (counter <= callsCount) {
            (bool success,) =
                xtzPrecompile.call{value: counter * 10 ** 12}(data);
            require(success, "Call to target contract failed");
            counter += 1;
        }
    }

    // TODO: explain that this function used to receive xtz
    receive() external payable {}
}
