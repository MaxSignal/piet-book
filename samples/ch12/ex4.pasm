; n の約数の個数
        inn             ; [n]
        push 0          ; [n c]
        pick 1          ; [n c d]        d を n から 1 まで減らす
loop:
        dup             ; [n c d d]
        jz done         ; [n c d]
        pick 2          ; [n c d n]
        pick 1          ; [n c d n d]
        mod             ; [n c d n%d]
        not             ; [n c d f]
        push 3
        push 2
        roll            ; [n d f c]      f = (n%d==0)
        add             ; [n d c']
        swap            ; [n c' d]
        push 1
        sub             ; [n c' d-1]
        jmp loop
done:
        pop
        outn
        push 10
        outc
