; 整数を 2 進数で出力する
        inn             ; [n]
        push 2
        swap            ; [2 n]          2 は番兵（桁は 0 か 1）
loop:
        dup
        push 2
        mod             ; [2 .. n b]
        swap
        push 2
        div             ; [2 .. b n/2]
        dup
        jnz loop        ; n/2 が 0 でなければ続ける
        pop             ; [2 b_k .. b_0]  上位の桁が先頭
print:
        dup
        push 2
        sub
        jz done         ; 番兵に着いた
        outn
        jmp print
done:
        push 10
        outc
