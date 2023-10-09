(* Context is set by implicit address before ticket send:
    - data is the data that will be added to the ticket
    - receiver is the address of the contract that will receive the ticket
*)

type 'data context_t = {
    data : 'data;
    receiver : address;
}

type 'data t = {
    context : (address, 'data context_t) big_map;
    metadata : (string, bytes) big_map;
}
