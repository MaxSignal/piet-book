; 正しく止まる版: 「0 より大きい間」繰り返す
  push 9
loop:
  dup
  outn
  push 10
  outc
  push 2
  sub
  dup
  push 0
  gt            ; n > 0 なら 1
  jnz loop
  pop
