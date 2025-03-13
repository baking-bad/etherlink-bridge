#import "../types/ticket.mligo" "Ticket"
#import "../errors.mligo" "Errors"


(*
    `settle-withdrawal` is the fast withdrawal interface used for processing
    XTZ-native tickets from the Etherlink rollup during fast withdrawals:

    - withdrawal_id: a unique identifier for the withdrawal,
    - ticket: the provided XTZ-native ticket to be burned,
    - timestamp: the time when withdrawal was applied on the Etherlink side,
    - base_withdrawer: the target receiver of the fast withdrawal,
    - payload: additional data containing the fast withdrawal conditions,
    - l2_caller: the original sender address on the Etherlink side.
 *)
type t = {
    withdrawal_id : nat;
    ticket : Ticket.t;
    timestamp : timestamp;
    base_withdrawer : address;
    payload : bytes;
    l2_caller : bytes;
}

let get (fast_withdrawal_contract : address) : t contract =
    match Tezos.get_entrypoint_opt "%default" fast_withdrawal_contract with
    | None -> failwith(Errors.settle_withdrawal_entrypoint_not_found)
    | Some entry -> entry

let send
        (fast_withdrawal_contract : address)
        (params : t)
        : operation =
    let entry = get fast_withdrawal_contract in
    Tezos.transaction params 0mutez entry
