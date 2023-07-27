module TicketStorage = struct
    (* This is contract example that can release tickets stored in bigmap *)

    type storage_t = (nat, string ticket) big_map
    type return_t = operation list * storage_t

    // [@entry] let deposit (ticket : string ticket) (store : storage_t) : return_t =
    // -- not implemented

    [@entry] let release (ticket_id : nat) (store : storage_t) : return_t =
        let ticket_opt = Big_map.find_opt ticket_id store in
        let ticket = Option.unopt ticket_opt in
        let sender = Tezos.get_sender () in
        let receiver_contract_opt = Tezos.get_contract_opt sender in
        let receiver_contract = Option.unopt receiver_contract_opt in
        let ticket_transfer_op = Tezos.transaction ticket 0mutez receiver_contract in

        // The following line fails to compile with ticket DUP error:
        [ticket_transfer_op], (Big_map.remove ticket_id store)

        // The following line works fine:
        // [ticket_transfer_op], (Big_map.empty : storage_t)
end

