; 入力した整数が正・ゼロ・負のどれかを表示する
  inn            ; [n]
  dup            ; [n n]
  jz zero        ; [n]
  push 0         ; [n 0]
  gt             ; [n>0]
  jnz positive
  prints "negative\n"
  halt
zero:
  prints "zero\n"
  halt
positive:
  prints "positive\n"
