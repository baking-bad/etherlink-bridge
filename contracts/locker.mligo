#import "./common/types.mligo" "Types"
#import "./common/errors.mligo" "Errors"


module Locker = struct
    (* This is helper contract used to lock/release tickets in the same
        way Rollup would do *)

    type ticket_ty = Types.payload ticket

    (*
    // NOTE: the following record with ticket fails to be compiled without
    //       ticket duplications
    type ticket_with_data_t = {
        string_ticket: ticket_ty;
        routing_data: Types.routing_data;
    }
    *)

    type ticket_with_data_t = ticket_ty * Types.routing_data

    type storage_t = ticket_with_data_t list
    type return_t = operation list * storage_t

    [@entry] let save (ticket_with_data : ticket_with_data_t) (store : storage_t) : return_t =
        [], ticket_with_data :: store

    [@entry] let release () (store : storage_t) : return_t =
        (* Releases all tickets from storage *)
        // TODO: consider release tickets by id?

        let send (ticket_with_data : ticket_with_data_t) : operation =
            let sr_ticket, _ = ticket_with_data in
            let receiver = Tezos.get_sender () in
            let receiver_contract: ticket_ty contract =
                match Tezos.get_contract_opt receiver with
                | None -> failwith Errors.failed_to_get_ticket_entrypoint
                | Some c -> c in
            let (_, (_, _)), read_ticket =
                Tezos.read_ticket sr_ticket in
            Tezos.transaction read_ticket 0mutez receiver_contract in

        List.map send store, ([] : storage_t)
end
