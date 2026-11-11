; 3+4=7 と出力する
  push 3
  dup
  outn           ; 3        [3]
  push 43
  outc           ; '+'      [3]
  push 4
  dup
  outn           ; 4        [3 4]
  push 61
  outc           ; '='      [3 4]
  add
  outn           ; 7        []
  push 10
  outc
