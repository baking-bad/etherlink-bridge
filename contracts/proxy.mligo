#import "./common/types.mligo" "Types"

module Proxy = struct
    (* This contract helps user to send tickets with external data to the
        contracts *)

    type ticket_ty = Types.payload ticket
    type data_t = address
    // TODO: type data_t = pair (bytes %data) (map %routing_info string bytes)
    // TODO: the same type used in locker, need to move this type to a separate module

    (* Context is set by implicit address before ticket send
        - data is the data that will be added to the ticket
        - receiver is the address of the contract that will receive the ticket
    *)
    type context_t = {
        data : data_t;
        receiver : address;
    }
    // TODO: is it required to have empty context? (and reset it after each send?)

    type ticket_with_data_t = ticket_ty * data_t
    type storage_t = context_t
    type return_t = operation list * storage_t

    [@entry] let set (ctx : context_t) (_ : storage_t) : return_t =
        [], ctx

    [@entry] let send_ticket (some_ticket : ticket_ty) (store : storage_t) : return_t =
        (* Resend ticket from user with data from the context
            to the receiver from the context *)

        let ctx = store in
        let receiver_contract: ticket_with_data_t contract =
        // TODO: is it possible to unhardcode entrypoint name?
        // (check this: Tezos.get_contract_opt with "KT...%save")
            match Tezos.get_entrypoint_opt "%save" ctx.receiver with
            | None -> failwith "FAILED_TO_GET_TICKET_ENTRYPOINT"
            | Some c -> c in
        let ticket_with_data : ticket_with_data_t =
            some_ticket, ctx.data in
        let op = Tezos.transaction ticket_with_data 0mutez receiver_contract in
        [op], store
end

