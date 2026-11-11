; 階乗 n! を計算して出力する
        inn             ; [n]
        push 1          ; [n acc]
loop:
        pick 1          ; [n acc n]
        jz done         ; [n acc]        n = 0 なら終わり
        pick 1          ; [n acc n]
        mul             ; [n acc*n]
        swap            ; [acc n]
        push 1
        sub             ; [acc n-1]
        swap            ; [n-1 acc]
        jmp loop
done:
        outn            ; [n]
        push 10
        outc            ; 改行
