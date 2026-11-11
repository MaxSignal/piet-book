; コラッツ数列を 1 になるまで出力する
        inn             ; [n]
loop:
        dup
        outn
        dup
        push 1
        sub
        jz done         ; n = 1 で終わり
        push 32
        outc            ; 区切りの空白
        dup
        push 2
        mod
        jz even
        push 3
        mul
        push 1
        add             ; [3n+1]
        jmp loop
even:
        push 2
        div             ; [n/2]
        jmp loop
done:
        push 10
        outc
