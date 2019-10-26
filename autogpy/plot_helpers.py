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


def latex_header_package_import(*args):
    """generates the string to import the desired latex package based on 
    their names.
    """

    typebased_op_support =\
        lambda entry_o :\
        {
            "str": lambda entry: r"\\usepackage{%s}" % entry
            , "tuple": lambda entry: r"\\usepackage[%s]{%s}" % (str(entry[0]), entry[1])
        }[type(entry_o).__name__]

    typebased_op = lambda x : typebased_op_support(x)(x)
    

    return "header " + "\"" + "\n".join(map(typebased_op, args)) + "\""


def load_gnuplotting_palette(palette_name, folder_dest):
    """Downloads palettes by name from Gnuplotting/gnuplot-palettes.
    """
    import requests
    BASIC_ADDRESS="https://raw.githubusercontent.com/Gnuplotting/gnuplot-palettes/master/"
    final_name = palette_name + '.pal'
    r = requests.get(BASIC_ADDRESS + final_name, allow_redirects=True)
    open(folder_dest + '/' + final_name, 'wb').write(r.content)

    return "load '%s'" % final_name


    
