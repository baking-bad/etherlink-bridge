#import "../common/errors.mligo" "Errors"
#import "./storage.mligo" "Storage"


(* This contract helps user to send tickets with external data to the
    contracts *)

type ('ticket, 'data) parameter_t = [@layout:comb]
    | Send_ticket of 'ticket
    | Set of 'data Storage.context_t


let set
        (type data_t)
        (ctx : data_t Storage.context_t)
        (store : data_t Storage.t)
        : operation list * data_t Storage.t =
    [], Big_map.update (Tezos.get_sender ()) (Some ctx) store


let send_ticket
        (type ticket_t data_t receiver_t)
        (some_ticket : ticket_t)
        (store : data_t Storage.t)
        (make_ctx : ticket_t * data_t -> receiver_t)
        : operation list * data_t Storage.t =
    (* Resend ticket from user with data from the context
        to the receiver from the context *)

    let ctx_opt = Big_map.find_opt (Tezos.get_sender ()) store in
    let ctx = match ctx_opt with
        | None -> failwith Errors.context_is_not_set
        | Some ctx -> ctx in
    let receiver_contract: receiver_t contract =
    // TODO: is it possible to unhardcode entrypoint name?
    // (check this: Tezos.get_contract_opt with "KT...%save")
        match Tezos.get_entrypoint_opt "%save" ctx.receiver with
        | None -> failwith Errors.failed_to_get_ticket_entrypoint
        | Some c -> c in
    // TODO: some function to make payload?
    let payload = make_ctx (some_ticket, ctx.data) in
    let op = Tezos.transaction payload 0mutez receiver_contract in
    [op], store


let main
        (type ticket_t data_t entrypoint_t)
        (make_ctx : ticket_t * data_t -> entrypoint_t)
        (params : (ticket_t, data_t) parameter_t)
        (store : data_t Storage.t)
        : operation list * data_t Storage.t =
    match params with
    | Send_ticket ticket -> send_ticket ticket store make_ctx
    | Set ctx -> set ctx store
