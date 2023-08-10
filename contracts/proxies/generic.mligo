#import "../common/errors.mligo" "Errors"
#import "./storage.mligo" "Storage"


(*
    Proxies is a collection of contracts that help implicit address to send
    tickets with external data to the contracts.

    Generic proxy contract allows to make proxies which allow different
    types of data to be attached to the different types of tickets,
    to be sended to the receiver.

    To create a proxy contract, you need to provide types of the ticket and
    external data added to the ticket, along with function that
    creates a per-user context for the ticket and the data.

    To use proxy, implicit address should first call `set` entrypoint
    to set the external data for the ticket and determine the receiver.
    Then, implicit address should call `send` entrypoint.
*)


type ('ticket, 'data) parameter_t = [@layout:comb]
    | Send of 'ticket
    | Set of 'data Storage.context_t


let set
        (type data_t)
        (ctx : data_t Storage.context_t)
        (store : data_t Storage.t)
        : operation list * data_t Storage.t =
    [], Big_map.update (Tezos.get_sender ()) (Some ctx) store


let send
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
        match Tezos.get_contract_opt ctx.receiver with
        | None -> failwith Errors.failed_to_get_ticket_entrypoint
        | Some c -> c in
    let payload = make_ctx (some_ticket, ctx.data) in
    let op = Tezos.transaction payload 0mutez receiver_contract in
    // TODO: need to clear context after each send for extra security
    [op], store


let main
        (type ticket_t data_t entrypoint_t)
        (make_ctx : ticket_t * data_t -> entrypoint_t)
        (params : (ticket_t, data_t) parameter_t)
        (store : data_t Storage.t)
        : operation list * data_t Storage.t =
    match params with
    | Send ticket -> send ticket store make_ctx
    | Set ctx -> set ctx store
