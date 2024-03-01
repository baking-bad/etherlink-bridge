// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

contract NativeWithdrawalPrecompile {
    function withdraw_base58(string memory target) public payable {}
}

contract NativeWithdrawalProxy {
    address precompile;

    constructor(address precompile_) {
        precompile = precompile_;
    }

    function withdraw_base58(string memory target) public payable {
        NativeWithdrawalPrecompile precompileContract =
            NativeWithdrawalPrecompile(precompile);
        precompileContract.withdraw_base58{value: msg.value}(target);
    }
}
