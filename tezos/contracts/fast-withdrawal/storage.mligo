#import "../common/types/fast-withdrawal.mligo" "FastWithdrawal"


type withdrawals = (FastWithdrawal.t, address) big_map

(*
    Fast Withdrawal contract storage:
    - exchanger: the address of the ticketer
    - smart_rollup: the address of the Etherlink smart rollup
    - withdrawals: stores service_provider for each withdrawal key
*)
type t = {
    exchanger: address;
    smart_rollup : address;
    withdrawals : withdrawals;
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
