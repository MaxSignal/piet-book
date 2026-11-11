; 絶対値: if (n < 0) n = 0 - n
  inn            ; [n]
  dup            ; [n n]
  push 0
  swap           ; [n 0 n]
  gt             ; [n 0>n]
  jz print       ; [n]
  push 0
  swap           ; [0 n]
  sub            ; [-n]
print:
  outn
  push 10
  outc
