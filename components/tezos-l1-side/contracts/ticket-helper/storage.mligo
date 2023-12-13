#import "../common/types/routing-data.mligo" "RoutingData"
#import "../common/tokens/index.mligo" "Token"


type t = [@layout:comb] {
    rollup : address;
    token : Token.t;
    ticketer : address;
    approve_amount : nat;
    routing_data : RoutingData.l1_to_l2_t option;

    // TODO: is there any sence to save routing_data per user in the BigMap?
    // The problem is that we don't know who are the sender when receiving
    // ticket from the Ticketer contract. However we can use the source.
    // routing_data : (address, RoutingData.l1_to_l2_t) big_map;
    metadata : (string, bytes) big_map;
}

let set_routing_data
        (routing_data : RoutingData.l1_to_l2_t)
        (store : t)
        : t =
    { store with routing_data = (Some routing_data) }

let clear_routing_data (store : t) : t = { store with routing_data = None }
