; 偶数なら E、奇数なら O を出力する
  inn
  push 2
  mod
  jz even
  prints "O"
  halt
even:
  prints "E"
