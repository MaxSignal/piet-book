; 九九の表（右寄せ 2 桁、空白区切り）
        push 1          ; [i]
row:
        push 1          ; [i j]
col:
        pick 1
        pick 1
        mul             ; [i j p]
        dup
        push 10
        swap
        gt              ; [i j p (10>p)]
        jz wide
        push 32
        outc            ; 1 桁なら空白を 1 つ足す
wide:
        outn            ; [i j]
        dup
        push 9
        sub
        jz endrow       ; j = 9 なら行の終わり
        push 32
        outc
        push 1
        add             ; [i j+1]
        jmp col
endrow:
        pop             ; [i]
        push 10
        outc
        dup
        push 9
        sub
        jz done
        push 1
        add
        jmp row
done:
        halt
