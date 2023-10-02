// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20} from "openzeppelin-contracts/token/ERC20/ERC20.sol";
import {BridgePrecompile} from "./BridgePrecompile.sol";

function hashToken(bytes20 ticketer, bytes memory identifier)
    pure
    returns (uint256)
{
    return uint256(keccak256(abi.encodePacked(ticketer, identifier)));
}

/**
 * ERC20 Wrapper is a ERC20 token contract which represents a L1 token
 * on L2.
 */
contract ERC20Wrapper is ERC20 {
    uint256 private _tokenHash;
    // TODO: when we have kernel address fixed at 0x00 in Etherlink L2 side
    //       we can remove this field from constructor.
    address private _kernel;
    address private _bridge;
    uint8 private _decimals;

    /**
     * @param ticketer_ whitelisted Tezos L1 address of the ticketer contract
     * @param identifier_ identifier of the L1 token (ticket id)
     * @param kernel_ address of the rollup kernel which is responsible for
     *        minting tokens
     * @param bridge_ address of the bridge precompile contract which is
     *        responsible for burning tokens and process withdrawals
     * @param name_ name of the token
     * @param symbol_ symbol of the token
     * @param decimals_ number of decimals of the token
     */
    constructor(
        bytes20 ticketer_,
        bytes memory identifier_,
        address kernel_,
        address bridge_,
        string memory name_,
        string memory symbol_,
        uint8 decimals_
    ) ERC20(name_, symbol_) {
        _tokenHash = hashToken(ticketer_, identifier_);
        _kernel = kernel_;
        _bridge = bridge_;
        _decimals = decimals_;
        this;
    }

    /**
     * Mints `amount` tokens for `to` address if provided `ticketer`
     * address and `identifier` are correct.
     *
     * Requirements:
     *
     * - only kernel address allowed to mint tokens.
     * - `tokenHash` must be equal to the token hash of the ticketer
     * and identifier used during deployment.
     */
    function deposit(address receiver, uint256 amount, uint256 tokenHash)
        public
    {
        require(
            _kernel == _msgSender(),
            "ERC20Wrapper: only kernel allowed to mint tokens"
        );
        require(_tokenHash == tokenHash, "ERC20Wrapper: wrong token hash");
        _mint(receiver, amount);
    }

    /**
     * Burns `amount` tokens from the caller's account and creates
     * transaction to withdraw `amount` tokens from L2 to L1.
     *
     * Requirements:
     *
     * - `amount` must be less or equal to the balance of the caller.
     */
    function withdraw(bytes20 receiver, uint256 amount) public {
        address from = _msgSender();
        _burn(from, amount);
        BridgePrecompile bridge = BridgePrecompile(_bridge);
        bridge.withdraw(from, receiver, amount, _tokenHash);
    }

    function decimals() public view override returns (uint8) {
        return _decimals;
    }

    // TODO: getTicketer, getIdentifier, getRollupKernel
}
