; limit 未満のフィボナッチ数を順に出力する
        inn             ; [lim]
        push 0          ; [lim a]
        push 1          ; [lim a b]
loop:
        pick 2          ; [lim a b lim]
        pick 2          ; [lim a b lim a]
        gt              ; [lim a b (lim>a)]
        jz done         ; [lim a b]
        pick 1          ; [lim a b a]
        outn            ; [lim a b]
        push 10
        outc
        dup             ; [lim a b b]
        bury 2          ; [lim b a b]
        add             ; [lim b a+b]
        jmp loop
done:
        halt
