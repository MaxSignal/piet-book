; 最小公倍数 lcm(a, b) = a * b / gcd(a, b)
        inn             ; [a]
        inn             ; [a b]
        pick 1          ; [a b a]
        pick 1          ; [a b a b]
        mul             ; [a b p]        p = a*b
        bury 2          ; [p a b]
loop:
        dup             ; [p a b b]
        jz done         ; [p a b]
        dup             ; [p a b b]
        bury 2          ; [p b a b]
        mod             ; [p b a%b]
        jmp loop
done:
        pop             ; [p g]
        div             ; [p/g]
        outn
        push 10
        outc
