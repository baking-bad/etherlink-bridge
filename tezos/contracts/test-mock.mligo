#import "./common/types/ticket.mligo" "Ticket"
#import "./common/entrypoints/router-withdraw.mligo" "WithdrawEntry"


module TicketerMock = struct
    (*
        This is helper contract used to communicate with L1 contract for testing
        purposes. It allows to test entrypoints that receive tickets.
    *)

    type storage_t = unit
    type return_t = operation list * storage_t

    type to_default_params = [@layout:comb] {
        payload : Ticket.content_t;
        amount : nat;
        receiver : address;
    }

    type to_router_params = [@layout:comb] {
        payload : Ticket.content_t;
        amount : nat;
        receiver : address;
        router : address;
    }

    [@entry] let to_default
            (params : to_default_params)
            (store : storage_t)
            : return_t =
        (*
            `to_default` mints ticket to the implicit address or contract
            default entrypoint. Resends any xtz attached to the call.
        *)

        let { payload; amount; receiver } = params in
        let ticket = Ticket.create payload amount in
        let receiver_contract = Ticket.get_ticket_entrypoint receiver in
        let amount = Tezos.get_amount () in
        let ticket_mint_op = Tezos.transaction ticket amount receiver_contract in
        [ticket_mint_op], store

    [@entry] let to_router
            (params : to_router_params)
            (store : storage_t)
            : return_t =
        (*
            `to_router` mints ticket to the smart contract which supports
            router `withdraw` interface. Resends any xtz attached to the call.
        *)

        let { payload; amount; receiver; router } = params in
        let ticket = Ticket.create payload amount in
        let receiver_contract = Ticket.get_ticket_entrypoint router in
        let amount = Tezos.get_amount () in
        let payload = { receiver; ticket } in
        let entry = WithdrawEntry.get router in
        let ticket_mint_op = Tezos.transaction payload amount entry in
        [ticket_mint_op], store
end