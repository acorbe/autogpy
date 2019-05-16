MAKEFILE_LATEX=\
"""
SHELL:=/bin/bash
latex_figs=$(wildcard *.pdflatex_compile.sh)
tikz_figs=$(wildcard *.tikz_compile.sh)
latex_targets_pdf=$(latex_figs:.pdflatex_compile.sh=.pdf)
tikz_targets_pdf=$(tikz_figs:.tikz_compile.sh=.tikz.pdf)
all_targets=$(latex_targets_pdf) $(tikz_targets_pdf)

all: $(all_targets)



%.tikz.pdf: %.tikz_compile.sh %.tikz.gnu %.core.gnu
{TAB}bash $<
{TAB}-[[ -f "compiled_files_redirection.string" ]] && (mkdir -p `cat compiled_files_redirection.string`)
{TAB}-[[ -f "compiled_files_redirection.string" ]] && (cp $@ `cat compiled_files_redirection.string`)


%.pdf: %.pdflatex_compile.sh %.pdflatex.gnu %.core.gnu
{TAB}bash $<
{TAB}-[[ -f "compiled_files_redirection.string" ]] && (mkdir -p `cat compiled_files_redirection.string`)
{TAB}-[[ -f "compiled_files_redirection.string" ]] && (cp $@ `cat compiled_files_redirection.string`)


clean:
{TAB}rm -f *.pdf *.jpg

deepclean:
{TAB}rm -rf *

.PHONY: sync
sync:
{TAB}bash sync_me.sh

""".format(TAB="\t")

SYNC_sc_template =\
"""
{SYNC_SCP_CALL}
"""

LATEX_compile_sh_template =\
"""
mkdir fig.latex.nice
gnuplot {LATEX_TARGET_GNU}

latex fig.latex.nice/plot_out.tex
dvips plot_out.dvi  -o plot_out.ps
ps2eps --ignoreBB -f plot_out.ps
ps2pdf plot_out.ps

mv plot_out.pdf {FINAL_PDF_NAME}
convert -density {pdflatex_jpg_convert_density} {FINAL_PDF_NAME} -quality {pdflatex_jpg_convert_quality} {FINAL_PDF_NAME_jpg_convert} 

rm *.aux || true
rm *.dvi || true
rm *.log || true
rm *.ps || true
"""

LATEX_wrapper_file=\
"""
set terminal epslatex size {x_size},{y_size} color colortext standalone \
     '{font}'  linewidth {linewidth}
set output 'fig.latex.nice/plot_out.tex'

load "{CORE}"; 
"""


TIKZ_wrapper_file=\
"""
set terminal tikz size {x_size},{y_size} color colortext standalone \
     '{font}'  linewidth {linewidth}
set output 'fig.latex.nice/tikz_out.tex'

load "{CORE}"; 
"""

TIKZ_compile_sh_template =\
"""
mkdir fig.latex.nice
gnuplot {TIKZ_TARGET_GNU}

pdflatex fig.latex.nice/tikz_out.tex
# dvips plot_out.dvi  -o plot_out.ps
# ps2eps --ignoreBB -f plot_out.ps
# ps2pdf plot_out.ps

mv tikz_out.pdf {FINAL_PDF_NAME}
convert -density {pdflatex_jpg_convert_density} {FINAL_PDF_NAME} -quality {pdflatex_jpg_convert_quality} {FINAL_PDF_NAME_jpg_convert} 

rm *.aux || true
rm *.log || true
"""


JPG_wrapper_file=\
"""
set term jpeg;
set out "{OUTFILE}";
load "{CORE}";       
         
"""





