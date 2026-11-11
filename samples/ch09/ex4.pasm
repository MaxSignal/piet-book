; 2 つの整数が等しいかどうか
  inn
  inn            ; [a b]
  sub            ; [a-b]
  jz equal
  push 33        ; '!'
  outc
  halt
equal:
  push 61        ; '='
  outc
