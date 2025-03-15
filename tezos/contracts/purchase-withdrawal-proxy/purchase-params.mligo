#import "../common/entrypoints/purchase-withdrawal.mligo" "PurchaseWithdrawalEntry"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/types/fast-withdrawal.mligo" "FastWithdrawal"


// TODO: add docstring
type t = {
    withdrawal : FastWithdrawal.t;
    service_provider : address;
    fast_withdrawal_contract : address;
    exchanger : address;
}

let to_purchase_withdrawal
        (ticket : Ticket.t)
        (purchase_withdrawal_proxy_entry : t)
        : PurchaseWithdrawalEntry.t =
    let {
        withdrawal;
        service_provider;
        fast_withdrawal_contract = _;
        exchanger = _;
    } = purchase_withdrawal_proxy_entry in
    {
        withdrawal;
        service_provider;
        ticket;
    }

