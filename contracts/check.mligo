module Check = struct
    (* This is temporal contract to check if ticket duplicated *)
    type storage_t = (nat, string ticket) big_map
    type return_t = operation list * storage_t

    [@entry] let check () (store : storage_t) : return_t =
        let ticket_id = 0n in
        let ticket_opt = Big_map.find_opt ticket_id store in
        let ticket = Option.unopt ticket_opt in
        // The following line fail to compile with DUP ticket instruction:
        let (_, (_, _)), ticket_copy = Tezos.read_ticket ticket in
        let sender = Tezos.get_sender () in
        let receiver_contract_opt = Tezos.get_contract_opt sender in
        let receiver_contract = Option.unopt receiver_contract_opt in
        let ticket_transfer_op = Tezos.transaction ticket_copy 0mutez receiver_contract in

        // [ticket_transfer_op], (big_map.remove ticket_id store)
        [ticket_transfer_op], (Big_map.empty : storage_t)
end

