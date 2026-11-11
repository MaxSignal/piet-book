; n 段の * の三角形（二重ループ）
  inn            ; [n]
  push 1         ; [n i]      i 段目（1 から）
row:
  dup            ; [n i i]
  pick 2         ; [n i i n]
  gt             ; [n i i>n]
  jnz end        ; [n i]
  dup            ; [n i k]    この段で残り k 個
star:
  dup            ; [n i k k]
  jz eol         ; [n i k]
  push 42        ; '*'
  outc
  push 1
  sub            ; [n i k-1]
  jmp star
eol:
  pop            ; [n i]
  push 10
  outc
  push 1
  add            ; [n i+1]
  jmp row
end:
  halt
