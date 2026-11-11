; FizzBuzz（1 から 100 まで）
        push 1          ; [i]
loop:
        dup
        push 15
        mod
        jz fb           ; 15 の倍数
        dup
        push 3
        mod
        jz f            ; 3 の倍数
        dup
        push 5
        mod
        jz b            ; 5 の倍数
        dup
        outn            ; それ以外は数そのもの
next:
        push 10
        outc
        push 1
        add             ; [i+1]
        dup
        push 101
        sub
        jnz loop        ; i+1 が 101 でなければ続ける
        halt
fb:
        prints "FizzBuzz"
        jmp next
f:
        prints "Fizz"
        jmp next
b:
        prints "Buzz"
        jmp next
