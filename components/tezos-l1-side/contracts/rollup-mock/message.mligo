#import "../common/types/routing-data.mligo" "RoutingData"
#import "./ticket-id.mligo" "TicketId"


(* Message is used to emulate L1->L2 outbox message
    - ticket_id is used to find L1 ticket in storage
    - amount of L1 ticket that should be unlocked
    - routing_data is info that will be used to route message to L1
    - router is address of L1 router contract that will be used to route message
*)
type t = {
    ticket_id : TicketId.t;
    amount : nat;
    routing_data : RoutingData.l2_to_l1_t;
}
