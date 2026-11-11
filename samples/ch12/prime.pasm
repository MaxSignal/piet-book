; n が素数かどうかを判定する（試し割り）
        inn             ; [n]
        push 2
        pick 1          ; [n 2 n]
        gt              ; [n (2>n)]
        jnz notprime    ; [n]            n < 2 は素数ではない
        push 2          ; [n d]
loop:
        dup             ; [n d d]
        dup             ; [n d d d]
        mul             ; [n d d*d]
        pick 2          ; [n d d*d n]
        gt              ; [n d (d*d>n)]
        jnz isprime     ; [n d]          d*d > n まで割り切れなかった
        pick 1          ; [n d n]
        pick 1          ; [n d n d]
        mod             ; [n d n%d]
        jz notprime     ; [n d]          割り切れた
        push 1
        add             ; [n d+1]
        jmp loop
isprime:
        prints "prime\n"
        halt
notprime:
        prints "not prime\n"
        halt
