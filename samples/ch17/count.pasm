; 3, 2, 1 と数える
  push 3
loop:
  dup
  outn
  push 1
  sub
  dup
  jnz loop
  pop
  halt
