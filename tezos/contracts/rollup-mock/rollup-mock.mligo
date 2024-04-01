#import "../common/entrypoints/router-withdraw.mligo" "RouterWithdrawEntry"
#import "../common/entrypoints/rollup-deposit.mligo" "RollupDepositEntry"
#import "./tickets.mligo" "Tickets"


module RollupMock = struct
    (*
        RollupMock is helper contract used to deposit and release tickets on
        the L1 side in the similar way Rollup would do.
    *)

    (*
        Storage of the RollupMock contract:
        - tickets: a big_map of tickets, keys are ticket ids and values are tickets
        - metadata: a big_map containing the metadata of the contract (TZIP-016), immutable
    *)
    type storage_t = {
        tickets : Tickets.t;
        metadata : (string, bytes) big_map;
    }

    type execute_params_t = {
        ticket_id : Tickets.id_t;
        amount : nat;
        receiver : address;
        router : address;
    }

    type return_t = operation list * storage_t

    [@entry] let rollup
            (rollup_entry : RollupDepositEntry.t)
            (store : storage_t)
            : return_t =
        (*
            `rollup` entrypoint emulates L1 rollup full entrypoint.
            It allows to deposit tickets the same way as L1 rollup would do.
            RollupMock saves provided tickets in the storage.

            @param rollup_entry: the full entrypoint of the Etherlink smart rollup
        *)

        let deposit = RollupDepositEntry.unwrap rollup_entry in
        let { ticket; routing_info = _r } = deposit in
        let { tickets; metadata } = store in
        let tickets = Tickets.save ticket tickets in
        let store = { tickets; metadata } in
        [], store

    [@entry] let execute_outbox_message
            (params : execute_params_t)
            (store : storage_t)
            : return_t =
        (*
            `execute_outbox_message` allows to release tickets the same way
            as L1 rollup would do when someone triggered L1 outbox message
            execution. It will call the withdraw router contract with the
            ticket and receiver address.

            The real L1 rollup `execute_outbox_message` is not an entrypoint
            but a special operation that requires `commitment` and `proof` to
            be provided instead of execution parameters as in this mock.

            @param ticket_id: a ticket id to release
            @param amount: an amount of the ticket to release
            @param receiver: an address that would be passed as a receiver
                to the router
            @param router: an address of the router (ticketer) contract
        *)

        let { tickets; metadata } = store in
        let { ticket_id; router; amount; receiver } = params in
        let ticket, tickets = Tickets.get ticket_id amount tickets in
        let withdraw_params = { ticket; receiver } in
        let withdraw_op = RouterWithdrawEntry.send router withdraw_params in
        let store = { tickets; metadata } in
        [withdraw_op], store
end
