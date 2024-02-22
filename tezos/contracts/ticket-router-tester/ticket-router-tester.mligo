#import "../common/types/routing-info.mligo" "RoutingInfo"
#import "../common/entrypoints/rollup-deposit.mligo" "RollupDepositEntry"
#import "../common/entrypoints/router-withdraw.mligo" "RouterWithdrawEntry"
#import "../common/types/ticket.mligo" "Ticket"


module TicketRouterTester = struct
    (*
        TicketRouterTester is a helper contract which helps developer to test
        Etherlink Bridge ticket layer protocol components. It provides
        a simple interface to deposit and withdraw tickets to and from
        Etherlink Bridge.

        This contract expected to be used only for testing purposes.
    *)

    type storage_t = [@layout:comb] {
        rollup : address;
        routing_info : RoutingInfo.l1_to_l2_t;
        metadata : (string, bytes) big_map;
    }
    type return_t = operation list * storage_t

    [@entry] let set
            (new_store : storage_t)
            (_store : storage_t) : return_t =
        [], new_store

    [@entry] let deposit
            (ticket : Ticket.t)
            (store : storage_t) : return_t =
        let { rollup; routing_info; metadata = _ } = store in
        let deposit = { routing_info; ticket } in
        [RollupDepositEntry.make rollup deposit], store

    [@entry] let withdraw
            (params : RouterWithdrawEntry.t)
            (store : storage_t) : return_t =
        let { receiver; ticket } = params in
        [Ticket.send ticket receiver], store
end
