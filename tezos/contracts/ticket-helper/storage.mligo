#import "../common/types/routing-info.mligo" "RoutingInfo"
#import "../common/tokens/index.mligo" "Token"


type context_t = [@layout:comb] {
    routing_info : RoutingInfo.l1_to_l2_t;
    rollup : address;
}

type t = [@layout:comb] {
    token : Token.t;
    ticketer : address;
    context : context_t option;
    metadata : (string, bytes) big_map;
}

let set_context
        (context : context_t)
        (store : t)
        : t =
    { store with context = (Some context) }

let clear_context (store : t) : t = { store with context = None }
