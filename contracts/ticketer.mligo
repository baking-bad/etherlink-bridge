module Ticketer = struct
  type storage = unit
  type token = unit
  type ticket = unit
  type return = operation list * storage

  [@entry] let deposit (store, token, amount : storage * token * nat) (store : storage) : return = [], store
  [@entry] let release (store, ticket, destination : storage * ticket * nat) (store : storage) : return = [], store
end
