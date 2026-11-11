; n x 1 = n から n x 9 = 9n まで
  inn            ; [n]
  push 1         ; [n k]
loop:
  dup
  push 9
  gt             ; [n k k>9]
  jnz end
  pick 1
  outn           ; n
  prints " x "
  dup
  outn           ; k
  prints " = "
  pick 1
  pick 1
  mul
  outn           ; n*k
  push 10
  outc
  push 1
  add
  jmp loop
end:
  halt
