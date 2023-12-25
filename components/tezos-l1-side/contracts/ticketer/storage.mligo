#import "../common/tokens/index.mligo" "Token"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/errors.mligo" "Errors"


type t = {
    metadata : (string, bytes) big_map;
    token : Token.t;
    content : Ticket.content_t;
}
