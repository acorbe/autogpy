
# BEGIN parameters

    set xlabel "$t$"
    set ylabel "$f(t)$"
    set key outside under
    
# END parameters



# this is multiplot idx: 0
p  "fig__0__.dat"  w l ls 4 lw 2 title "$\\frac{1}{2} t$" ,\
 "fig__1__.dat"  u 1:2:3 every 3 w yerr ls 2 lw 2 title "$1.5 \\cos t$" 