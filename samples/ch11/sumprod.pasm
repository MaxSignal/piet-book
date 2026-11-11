; 1..n の和と積を同時に求める。スタックを [i s p] の「変数」として使う
  inn            ; [i]        i = n から 1 まで数え下げる
  push 0         ; [i s]
  push 1         ; [i s p]
loop:
  pick 2         ; [i s p i]
  jz done        ; [i s p]
  pick 2         ; [i s p i]
  mul            ; [i s p*i]
  push 3
  push 2
  roll           ; [s p i]     rot: i を先頭へ
  dup            ; [s p i i]
  push 4
  push 3
  roll           ; [p i i s]   s を先頭へ（roll 4 3 = 4 段の rot）
  add            ; [p i s+i]
  push 3
  push 1
  roll           ; [s p i]     -rot
  push 1
  sub            ; [s p i-1]
  push 3
  push 1
  roll           ; [i-1 s p]
  jmp loop
done:
  push 2
  push 1
  roll           ; [i p s]
  outn           ; s
  push 32
  outc
  outn           ; p
  push 10
  outc
