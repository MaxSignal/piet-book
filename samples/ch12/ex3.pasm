; 整数平方根: r*r <= n をみたす最大の r
        inn             ; [n]
        push 0          ; [n r]
loop:
        dup             ; [n r r]
        push 1
        add             ; [n r r+1]
        dup
        mul             ; [n r (r+1)^2]
        pick 2          ; [n r (r+1)^2 n]
        gt              ; [n r ((r+1)^2 > n)]
        jnz done        ; [n r]
        push 1
        add             ; [n r+1]
        jmp loop
done:
        outn
        push 10
        outc
