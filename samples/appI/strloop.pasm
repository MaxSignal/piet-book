; 番兵 0 と逆順の文字を積み、0 が出るまで出力する
  push 0         ; 番兵
  push 10        ; 改行
  push 105       ; i
  push 72        ; H
loop:
  dup
  jz done
  outc
  jmp loop
done:
  pop
