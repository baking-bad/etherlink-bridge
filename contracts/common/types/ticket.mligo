#import "../errors.mligo" "Errors"


type payload_t = [@layout:comb] {
    token_id : nat;
    token_info : bytes option;
}

type t = payload_t ticket


let create_ticket
        (payload : payload_t)
        (amount : nat)
        : t =
    match Tezos.create_ticket (payload) amount with
    | None -> failwith Errors.ticket_creation_failed
    | Some t -> t

let get_ticket_entrypoint
        (address : address)
        : t contract =
    match Tezos.get_contract_opt address with
    | None -> failwith Errors.failed_to_get_ticket_entrypoint
    | Some c -> c

let create_l2_payload
        (payload : payload_t)
        (_ticketer : address)
        (l2_id : nat)
        : payload_t =
    // TODO: patch payload.token_info and add ticketer and L1 ticketer id to it
    //       reuse common/tokens/index.mligo as Token with Token.token_info
    let token_info = payload.token_info in {
        token_id = l2_id;
        token_info = token_info;
    }
