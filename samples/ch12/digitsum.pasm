; 各桁の数字の和を求める
        inn             ; [n]
        push 0          ; [n s]
loop:
        pick 1          ; [n s n]
        jz done         ; [n s]
        pick 1          ; [n s n]
        push 10
        mod             ; [n s d]        d = n % 10
        add             ; [n s+d]
        swap            ; [s n]
        push 10
        div             ; [s n/10]
        swap            ; [n/10 s]
        jmp loop
done:
        outn
        push 10
        outc
