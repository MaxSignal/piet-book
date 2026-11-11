; 前の文字との差を使って Hello, World! を出力する
  push 72      ; 'H'
  dup
  outc
  push 29      ; 72 + 29 = 101 'e'
  add
  dup
  outc
  push 7       ; 108 'l'
  add
  dup
  outc
  dup
  outc         ; 'l'
  push 3       ; 111 'o'
  add
  dup
  outc
  push 44      ; ','
  outc
  push 32      ; ' '
  outc
  push 87      ; 'W'
  outc
  dup
  outc         ; 'o'（スタックには 111 が残っている）
  push 3       ; 114 'r'
  add
  dup
  outc
  push 6       ; 108 'l'
  sub
  dup
  outc
  push 8       ; 100 'd'
  sub
  outc
  push 33      ; '!'
  outc
  push 10
  outc
