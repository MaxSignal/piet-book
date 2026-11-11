; コラッツ数列が 1 に達するまでの手数を数える
        inn             ; [n]
        push 0          ; [n c]
loop:
        pick 1          ; [n c n]
        push 1
        sub             ; [n c n-1]
        jz done         ; [n c]          n = 1 なら終わり
        push 1
        add             ; [n c+1]
        swap            ; [c n]
        dup             ; [c n n]
        push 2
        mod             ; [c n n%2]
        jz even         ; [c n]
        push 3
        mul
        push 1
        add             ; [c 3n+1]
        swap            ; [3n+1 c]
        jmp loop
even:
        push 2
        div             ; [c n/2]
        swap            ; [n/2 c]
        jmp loop
done:
        outn
        push 10
        outc
