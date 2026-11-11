; n の階乗
  inn            ; [n]
  push 1         ; [n f]
loop:
  pick 1         ; [n f n]
  jz done        ; [n f]
  pick 1         ; [n f n]
  mul            ; [n f*n]
  swap
  push 1
  sub
  swap           ; [n-1 f*n]
  jmp loop
done:
  outn
  push 10
  outc
