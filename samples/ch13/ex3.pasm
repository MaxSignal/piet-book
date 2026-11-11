; 整数を 8 進数で出力する
        inn             ; [n]
        push 8
        swap            ; [8 n]          8 は番兵（桁は 0〜7）
loop:
        dup
        push 8
        mod             ; [8 .. n d]
        swap
        push 8
        div             ; [8 .. d n/8]
        dup
        jnz loop
        pop
print:
        dup
        push 8
        sub
        jz done
        outn
        jmp print
done:
        push 10
        outc
