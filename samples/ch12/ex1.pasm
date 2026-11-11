; 1 から n までの和
        inn             ; [n]
        push 0          ; [n s]
loop:
        pick 1          ; [n s n]
        jz done         ; [n s]
        pick 1          ; [n s n]
        add             ; [n s+n]
        swap            ; [s n]
        push 1
        sub             ; [s n-1]
        swap            ; [n-1 s]
        jmp loop
done:
        outn
        push 10
        outc
