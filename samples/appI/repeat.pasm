; n 回 * を出力する（n は入力）
  inn            ; [n]
loop:
  dup            ; [n n]
  jz done        ; [n]
  push 42
  outc           ; * を出力
  push 1
  sub            ; [n-1]
  jmp loop
done:
  pop
