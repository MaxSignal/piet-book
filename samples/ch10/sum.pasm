; 1 から n までの和を求める
  inn            ; [n]
  push 0         ; [n s]
loop:
  pick 1         ; [n s n]
  jz done        ; [n s]       n が 0 なら終わり
  pick 1         ; [n s n]
  add            ; [n s+n]
  swap           ; [s n]
  push 1
  sub            ; [s n-1]
  swap           ; [n-1 s]
  jmp loop
done:
  outn           ; 和を出力
  push 10
  outc
