#import "./fa2.mligo" "TokenFa2"
#import "./fa12.mligo" "TokenFa12"
#import "../errors.mligo" "Errors"


type token_info_t = (string, bytes) map

type t =
    | Fa12 of TokenFa12.t
    | Fa2 of TokenFa2.t

let get_transfer_op
        (token: t)
        (amount: nat)
        (from_: address)
        (to_: address)
        : operation =
    match token with
    | Fa12 addr -> TokenFa12.get_transfer_op from_ to_ addr amount
    | Fa2 (addr, token_id) -> begin
        let txs = [
            {
                to_ = to_;
                token_id = token_id;
                amount = amount;
            }
        ] in
        TokenFa2.get_transfer_op from_ addr txs
    end

let get_approve_ops
        (token: t)
        (operator: address)
        (amount: nat)
        : operation list =
    match token with
    | Fa12 contract_address ->
        [
            TokenFa12.get_approve_op contract_address operator 0n;
            TokenFa12.get_approve_op contract_address operator amount;
        ]
    | Fa2 (contract_address, token_id) ->
        [ TokenFa2.get_approve_op contract_address token_id operator ]

// NOTE: the following functions is not used in the current ticketer
// implementation, however they might be useful in the future
// (for example, for the ticketer factory)

(*
let make_token_info
        (token : t)
        : token_info_t =
    match token with
    | Fa12 addr -> Map.literal [
        ("contract_address", Bytes.pack addr);
        ("token_type", Bytes.pack "FA1.2");
    ]
    | Fa2 (addr, token_id) -> Map.literal [
        ("contract_address", Bytes.pack addr);
        ("token_type", Bytes.pack "FA2");
        ("token_id", Bytes.pack token_id);
    ]

let unopt_token_info
        (token_info : bytes option)
        : token_info_t =
    match token_info with
    | None -> Map.empty
    | Some token_info_bytes -> (
        match Bytes.unpack token_info_bytes with
        | None -> failwith Errors.wrong_token_info_format
        | Some token_info -> token_info
    )

let merge_token_info
        (token_info_a : token_info_t)
        (token_info_b : token_info_t)
        : token_info_t =
    let fold_info = fun (acc, key_value : (token_info_t * (string * bytes))) ->
        let (key, value) = key_value in
        Map.add key value acc in
    Map.fold fold_info token_info_a token_info_b
*)
