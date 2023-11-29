// SPDX-License-Identifier: MIT
pragma solidity >=0.8.21;

import {ERC20} from "openzeppelin-contracts/token/ERC20/ERC20.sol";

function hashToken(bytes20 ticketer, bytes memory identifier)
    pure
    returns (uint256)
{
    // TODO: consider replacing encodePacked with encode:
    //       looks like type collision is impossible here, but
    //       maybe it is better to use encode? [1]
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
    uint8 private _decimals;

    /**
     * @param ticketer_ whitelisted Tezos L1 address of the ticketer contract
     * @param identifier_ identifier of the L1 token (ticket id)
     * @param kernel_ address of the rollup kernel which is responsible for
     *        minting and burning tokens
     * @param name_ name of the token
     * @param symbol_ symbol of the token
     * @param decimals_ number of decimals of the token
     */
    constructor(
        bytes20 ticketer_,
        bytes memory identifier_,
        address kernel_,
        string memory name_,
        string memory symbol_,
        uint8 decimals_
    ) ERC20(name_, symbol_) {
        _tokenHash = hashToken(ticketer_, identifier_);
        _kernel = kernel_;
        _decimals = decimals_;
        this;
    }

    /**
     * Checks if the sender is the kernel address.
     */
    function _requireSenderIsKernel() internal view {
        require(
            _kernel == _msgSender(),
            "ERC20Wrapper: only kernel allowed to mint / burn tokens"
        );
    }

    /**
     * Checks if the provided `tokenHash` is equal to the token hash
     * of the ticketer and identifier used during token deployment.
     */
    function _requireTokenHash(uint256 tokenHash) internal view {
        require(_tokenHash == tokenHash, "ERC20Wrapper: wrong token hash");
    }

    /**
     * Mints `amount` tokens for `to` address if provided `tokenHash`
     * is correct.
     *
     * Requirements:
     *
     * - only kernel address allowed to mint tokens.
     * - `tokenHash` must be equal to the token hash of the ticketer
     * and identifier used during deployment.
     */
    function mint(address account, uint256 value, uint256 tokenHash) public {
        _requireSenderIsKernel();
        _requireTokenHash(tokenHash);
        _mint(account, value);
    }

    /**
     * Burns `amount` tokens from the `from` address if provided `tokenHash`.
     * is correct.
     *
     * Requirements:
     *
     * - only kernel address allowed to burn tokens.
     * - `tokenHash` must be equal to the token hash of the ticketer
     * and identifier used during deployment.
     * - `amount` must be less or equal to the balance of the caller.
     */
    function burn(address account, uint256 value, uint256 tokenHash) public {
        _requireSenderIsKernel();
        _requireTokenHash(tokenHash);
        _burn(account, value);
    }

    function decimals() public view override returns (uint8) {
        return _decimals;
    }

    // TODO: consider adding getTokenHash() public view returns (uint256)?
}
