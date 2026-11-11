; 9 から 2 ずつ減らして 0 になったら止まる……はずが
  push 9
loop:
  dup
  outn
  push 10
  outc
  push 2
  sub
  dup
  jnz loop      ; 0 にならないので永久に回る
  pop
