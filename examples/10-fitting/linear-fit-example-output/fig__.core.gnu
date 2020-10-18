



# this is multiplot idx: 0
foo(x)=a*x+bq
fit foo(x) "fig__1__fit.dat" via a,bq
p  "fig__0__.dat"  title "data" ,\
  foo(x) title "fit" 