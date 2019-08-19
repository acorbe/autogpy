set_format_xy_latex_ndig = lambda ax, ndig = 1: \
    r"set format {ax} '$%.{ndig}f$'".format(ax=ax, ndig=ndig)

set_format_xy_latex_pow10_ndig = lambda ax, ndig = 1: \
    r"set format %s '$10^{{%.%df}}$'"%(ax, ndig)

set_preamble_autostyle1 = \
r"""
set mxtics 2
set mytics 1

# color definitions
set border linewidth 1.5
set style line 1 lc rgb '#ff0000'  lt 1 lw 2
#set style line 2 lc rgb '#ff0000' lt 1 lw 2
set style line 2 lc rgb '#0000ff' lt 3 lw 4

# Axes
set style line 11  lc rgb '#100100100' lt 1
set border 3 back ls 11
set tics nomirror out scale 0.75
# Grid
set style line 12 lc rgb'#808080' lt 0 lw 1
set grid back ls 12

unset grid
"""
