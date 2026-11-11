; 1 から n までを 1 行に 1 つずつ出力する
  inn            ; [n]
  push 1         ; [n i]
loop:
  dup            ; [n i i]
  pick 2         ; [n i i n]
  gt             ; [n i i>n]
  jnz end
  dup
  outn
  push 10
  outc
  push 1
  add            ; [n i+1]
  jmp loop
end:
  halt
