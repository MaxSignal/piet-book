; a*b + b*c + c*a
  inn
  inn
  inn            ; [a b c]
  pick 2         ; [a b c a]
  pick 2         ; [a b c a b]
  mul            ; [a b c ab]
  pick 2         ; [a b c ab b]
  pick 2         ; [a b c ab b c]
  mul
  add            ; [a b c ab+bc]
  pick 1         ; [a b c t c]
  pick 4         ; [a b c t c a]
  mul
  add            ; [a b c ab+bc+ca]
  outn
  push 10
  outc
