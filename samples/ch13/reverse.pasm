; 1 行を読んで逆順に出力する
        push 0          ; [0]            底の番兵
read:
        push 0
        inc             ; [0 .. 0 c] または [0 .. 0]
        dup
        jz eof
        swap
        pop             ; [0 .. c]
        dup
        push 10
        sub             ; [0 .. c c-10]
        jz newline      ; 改行なら読み込み終了
        jmp read
newline:
        pop             ; 改行を捨てる
        jmp print
eof:
        pop             ; EOF 検出用の 0 を捨てる
print:
        dup
        jz done         ; 底の番兵に着いた
        outc
        jmp print
done:
        push 10
        outc
