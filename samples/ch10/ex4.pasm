; 入力の文字数を数える
  push 0         ; [count]
loop:
  push 0         ; [count 0]      番兵
  inc            ; [count 0 c] または [count 0]
  dup
  not            ; c が読めなかった（先頭が 0）なら 1
  jnz done
  pop
  pop            ; [count]
  push 1
  add            ; [count+1]
  jmp loop
done:
  pop            ; [count]
  outn
  push 10
  outc
