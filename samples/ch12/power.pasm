; a の b 乗を計算する
        inn             ; [a]
        inn             ; [a b]
        push 1          ; [a b r]
loop:
        pick 1          ; [a b r b]
        jz done         ; [a b r]
        pick 2          ; [a b r a]
        mul             ; [a b r*a]
        swap            ; [a r b]
        push 1
        sub             ; [a r b-1]
        swap            ; [a b-1 r]
        jmp loop
done:
        outn
        push 10
        outc
