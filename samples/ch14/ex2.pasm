; FizzBuzz 別解: Fizz と Buzz を別々に判定し、どちらも出なければ数を出す
        push 1          ; [i]
loop:
        push 0          ; [i k]          k = 何か出力したか
        pick 1
        push 3
        mod
        jnz nofizz
        prints "Fizz"
        push 1
        add             ; k = k + 1
nofizz:
        pick 1
        push 5
        mod
        jnz nobuzz
        prints "Buzz"
        push 1
        add
nobuzz:
        jnz next        ; k ≠ 0 なら数は出さない
        dup
        outn
next:
        push 10
        outc
        push 1
        add
        dup
        push 101
        sub
        jnz loop
