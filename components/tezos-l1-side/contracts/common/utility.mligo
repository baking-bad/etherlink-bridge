#import "./errors.mligo" "Errors"


let assert_address_is_self
        (address : address)
        : unit =
    if address <> Tezos.get_self_address ()
    then failwith Errors.unauthorized_ticketer else unit
