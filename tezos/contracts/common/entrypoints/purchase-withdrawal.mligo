#import "../types/ticket.mligo" "Ticket"
#import "../errors.mligo" "Errors"


// TODO: add docstring
type t = {
    withdrawal_id : nat;
    ticket : Ticket.t;
    timestamp : timestamp;
    base_withdrawer : address;
    payload : bytes;
    l2_caller : bytes;
    service_provider : address;
    withdrawal_amount : nat;
}

let get (fast_withdrawal_contract : address) : t contract =
    match Tezos.get_entrypoint_opt "%purchase_withdrawal" fast_withdrawal_contract with
    | None -> failwith(Errors.purchase_withdrawal_entrypoint_not_found)
    | Some entry -> entry

let send
        (fast_withdrawal_contract : address)
        (params : t)
        : operation =
    let entry = get fast_withdrawal_contract in
    Tezos.Next.Operation.transaction params 0mutez entry
