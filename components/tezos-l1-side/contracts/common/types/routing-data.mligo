// TODO: consider renaming file to RoutingInfo


// L1 to L2 routing info is concatenated Etherlink addresses of
// (ticket_receiver, receiver) each 22 bytes long
type l1_to_l2_t = bytes

// L2 to L1 routing info is concatenated address of (router, receiver)
// each 20 bytes long
type l2_to_l1_t = bytes

// NOTE: in this rollup mock implementation receiver info is simplified
// and represented as a single address, the router address set
// during creation of the mock outbox message and stored in the rollup mock:
let get_receiver_l2_to_l1 (receiver : l2_to_l1_t) : address =
    Option.unopt (Bytes.unpack receiver)

// TODO: consider parsing the receiver and router addresses from the
// routing_data instead?
