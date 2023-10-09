#import "../errors.mligo" "Errors"

type t = address * nat

type transfer_txs_item = [@layout:comb] {
    to_: address;
    token_id: nat;
    amount: nat;
}

type transfer_txs = transfer_txs_item list

type transfer_params = [@layout:comb] {
    from_: address;
    txs: transfer_txs;
} list

let get_transfer_op
        (from_: address)
        (addr: address)
        (txs: transfer_txs)
        : operation =
    match Tezos.get_entrypoint_opt "%transfer" addr with
    | None -> failwith Errors.invalid_fa2
    | Some c ->
        let params = [{ from_ = from_; txs = txs }] in
        Tezos.transaction params 0mutez c
