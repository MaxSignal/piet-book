; 1 と 2^32 + 5 を積み、swap（深さ 2 の roll）してから両方を出力する
  push 1
  push 256
  dup
  mul
  dup
  mul          ; 2^32
  push 5
  add          ; 4294967301
  swap
  outn
  push 32
  outc
  outn
