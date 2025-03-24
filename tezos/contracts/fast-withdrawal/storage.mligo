#import "../common/types/fast-withdrawal.mligo" "FastWithdrawal"


type withdrawals = (FastWithdrawal.t, address) big_map

(*
    Fast Withdrawal contract storage:
    - exchanger: the address of the native XTZ ticketer
    - smart_rollup: the address of the Etherlink smart rollup
    - withdrawals: maps each withdrawal key to a service provider
    - expiration_seconds: number of seconds during which a withdrawal can be purchased at a discount
*)
type t = {
    // TODO: consider renaming to native_ticketer
    exchanger : address;
    smart_rollup : address;
    withdrawals : withdrawals;
    expiration_seconds : int;
}

let add_withdrawal
        (withdrawal : FastWithdrawal.t)
        (service_provider : address)
        (storage : t) : t =
    let updated_withdrawals = Big_map.add withdrawal service_provider storage.withdrawals in
    { storage with withdrawals = updated_withdrawals }

[@inline]
let assert_withdrawal_was_not_paid_before
        (withdrawal : FastWithdrawal.t)
        (storage : t) : unit =
    if Option.is_some (Big_map.find_opt withdrawal storage.withdrawals) then
        failwith "The fast withdrawal was already payed"
