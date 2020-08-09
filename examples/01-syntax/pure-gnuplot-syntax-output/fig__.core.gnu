
# BEGIN parameters

    set xlabel "$t$"
    set ylabel "$f(t)$"
    set key outside under
    
# END parameters



# this is multiplot idx: 0
p  "fig__0__.dat" with lines title "$\\frac{1}{2} t$" ls 4 lw 2,\
 "fig__1__.dat" using 1:2:3 every 3 with yerr title "$1.5 \\cos t$" ls 2 lw 2