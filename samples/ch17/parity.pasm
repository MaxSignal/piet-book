; 数を 1 つ読み、偶数なら even、奇数なら odd と出力する
  inn
  push 2
  mod
  jz even
  prints "odd\n"
  halt
even:
  prints "even\n"
