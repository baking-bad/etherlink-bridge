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

type operator_param_t = [@layout:comb] {
    owner: address;
    operator: address;
    token_id: nat;
}

type update_operator_param_t = [@layout:comb]
    | Add_operator of operator_param_t
    | Remove_operator of operator_param_t

type update_operator_params_t = update_operator_param_t list

let get_approve_op
        (contract_address: address)
        (token_id: nat)
        (spender: address)
        : operation =
    let entry_option = Tezos.get_entrypoint_opt "%update_operators" contract_address in
    let operator_param = {
        owner = Tezos.get_self_address ();
        operator = spender;
        token_id = token_id;
    } in
    let params = [Add_operator(operator_param)] in
    match entry_option with
    | None -> failwith Errors.invalid_fa2
    | Some entry -> Tezos.transaction params 0mutez entry
