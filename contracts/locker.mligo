module Locker = struct
    (* This is helper contract used to lock/release tickets in the same
        way Rollup would do *)

    // TODO: update payload and use the same payload as Ticketer does
    type ticket_ty = string ticket

    (*
    // NOTE: the following record with ticket fails to be compiled without
    //       ticket duplications
    type ticket_with_data_t = {
        string_ticket: ticket_ty;
        data: address;
    }
    *)

    type data_t = address
    type ticket_with_data_t = ticket_ty * data_t

    type storage_t = ticket_with_data_t list
    type return_t = operation list * storage_t

    [@entry] let save (ticket_with_data : ticket_with_data_t) (store : storage_t) : return_t =
        [], ticket_with_data :: store

    [@entry] let release () (store : storage_t) : return_t =
        (* Releases all tickets from storage *)
        // TODO: consider release tickets by id?
        // TODO: do not rely on receiver added to the data, return to the sender

        let send (ticket_with_data : ticket_with_data_t) : operation =
            let ticket_string, receiver = ticket_with_data in
            let receiver_contract: ticket_ty contract =
                match Tezos.get_contract_opt receiver with
                | None -> failwith "FAILED_TO_GET_TICKET_ENTRYPOINT"
                | Some c -> c in
            let (_, (_, _)), read_ticket =
                Tezos.read_ticket ticket_string in
            Tezos.transaction read_ticket 0mutez receiver_contract in

        List.map send store, ([] : storage_t)
end
