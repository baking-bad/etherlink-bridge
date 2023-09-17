#import "../errors.mligo" "Errors"

type t = address

type transfer_params = [@layout:comb] {
    [@annot:from] from_: address;
    [@annot:to] to_: address;
    value: nat;
}

let get_transfer_op
        (from_: address)
        (to_: address)
        (addr: address)
        (value: nat)
        : operation =
    match Tezos.get_entrypoint_opt "%transfer" addr with
    | None -> failwith Errors.invalid_fa12
    | Some c ->
        let params = {
            from_ = from_;
            to_ = to_;
            value = value
        } in
        Tezos.transaction params 0mutez c
