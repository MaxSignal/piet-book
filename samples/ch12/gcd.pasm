; ユークリッドの互除法で最大公約数を求める
        inn             ; [a]
        inn             ; [a b]
loop:
        dup             ; [a b b]
        jz done         ; [a b]          b = 0 なら a が答え
        dup             ; [a b b]
        bury 2          ; [b a b]
        mod             ; [b a%b]
        jmp loop
done:
        pop             ; [a]
        outn
        push 10
        outc
