#import "../types/ticket.mligo" "Ticket"
#import "../types/fast-withdrawal.mligo" "FastWithdrawal"
#import "../errors.mligo" "Errors"


// TODO: add docstring
type t = {
    withdrawal : FastWithdrawal.t;
    service_provider : address;
    ticket : Ticket.t;
}

let get (fast_withdrawal_contract : address) : t contract =
    match Tezos.get_entrypoint_opt "%purchase_withdrawal" fast_withdrawal_contract with
    | None -> failwith(Errors.purchase_withdrawal_entrypoint_not_found)
    | Some entry -> entry

let send
        (fast_withdrawal_contract : address)
        (params : t) : operation =
    let entry = get fast_withdrawal_contract in
    Tezos.Next.Operation.transaction params 0mutez entry
