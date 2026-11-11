; 入力の終わりまで 1 文字ずつ写す
loop:
  push 0         ; 読めなかったときに残る番兵
  inc            ; [0 c] または [0]
  dup
  jz done        ; 先頭が 0 なら入力の終わり
  outc           ; [0]
  pop            ; []
  jmp loop
done:
  pop
