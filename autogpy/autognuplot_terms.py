MAKEFILE_LATEX=\
"""
SHELL:=/bin/bash
latex_figs=$(wildcard *.pdflatex_compile.sh)
tikz_figs=$(wildcard *.tikz_compile.sh)
latex_targets_pdf=$(latex_figs:.pdflatex_compile.sh=.pdf)
tikz_targets_pdf=$(tikz_figs:.tikz_compile.sh=.tikz.pdf)
all_targets=$(latex_targets_pdf) $(tikz_targets_pdf)


all: {ALL_TARGETS}
latex: $(latex_targets_pdf)
tikz:  $(tikz_targets_pdf)


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
{TAB}rm -Rf fig.latex.nice
{TAB}rm -Rf fig.tikz.nice

deepclean:
{TAB}rm -rf *

.PHONY: sync
sync:
{TAB}bash sync_me.sh

""" #.format(TAB="\t")

SYNC_sc_template =\
"""
{SYNC_SCP_CALL}
"""

LATEX_compile_sh_template =\
"""
mkdir -p fig.latex.nice
gnuplot {LATEX_TARGET_GNU} || exit 1

latex fig.latex.nice/plot_out.tex
dvips plot_out.dvi  -o plot_out.ps
ps2eps --ignoreBB -f plot_out.ps
ps2pdf plot_out.ps

mv plot_out.pdf {FINAL_PDF_NAME}

if command -v pdftoppm &> /dev/null
then

    pdftoppm -png {FINAL_PDF_NAME} > {FINAL_PDF_NAME_jpg_convert}

else
## this step converts in jpg for displaying the image in jupyter
if convert -density {pdflatex_jpg_convert_density} {FINAL_PDF_NAME} -quality {pdflatex_jpg_convert_quality} {FINAL_PDF_NAME_jpg_convert} 
then
  echo "conversion successful"
else
  echo ""
  echo "-ERROR: The convert command gave an error."
  echo "-FIXES: Make sure imagemagick is installed"
  echo "        Make sure imagemagick enables offline conversions:"
  echo "          sudo sed -i '/PDF/s/none/read|write/' /etc/ImageMagick-6/policy.xml   "
  echo "        Ref:   https://stackoverflow.com/a/52661288"
  echo ""
fi
fi

rm *.aux || true
rm *.dvi || true
rm *.log || true
rm *.ps || true
rm -Rf fig.latex.nice || true
"""

LATEX_wrapper_file=\
"""
set terminal epslatex size {x_size},{y_size} color colortext standalone \
     '{font}'  linewidth {linewidth} {other}
set output 'fig.latex.nice/plot_out.tex'

load "{CORE}"; 
"""


TIKZ_wrapper_file=\
"""
set terminal tikz size {x_size},{y_size} color colortext standalone \
     '{font}'  linewidth {linewidth} {other}
set output 'fig.tikz.nice/tikz_out.tex'

load "{CORE}"; 
"""

TIKZ_compile_sh_template =\
"""
mkdir -p fig.tikz.nice
gnuplot {TIKZ_TARGET_GNU} || exit 1

pdflatex fig.tikz.nice/tikz_out.tex

mv tikz_out.pdf {FINAL_PDF_NAME}

## check if pdftoppm exists, usually gives better results
if command -v pdftoppm &> /dev/null
then

    pdftoppm -png {FINAL_PDF_NAME} > {FINAL_PDF_NAME_jpg_convert}

else
if convert -density {pdflatex_jpg_convert_density} {FINAL_PDF_NAME} -quality {pdflatex_jpg_convert_quality} {FINAL_PDF_NAME_jpg_convert} 
then
  echo "conversion successful"
else
  echo ""
  echo "-ERROR: The convert command gave an error."
  echo "-FIXES: Make sure imagemagick is installed"
  echo "        Make sure imagemagick enables offline conversions:"
  echo "          sudo sed -i '/PDF/s/none/read|write/' /etc/ImageMagick-6/policy.xml   "
  echo "        Ref:   https://stackoverflow.com/a/52661288"
  echo ""
fi

fi


rm *.aux || true
rm *.log || true
rm -Rf fig.tikz.nice || true
"""


JPG_wrapper_file=\
"""
set term jpeg;
set out "{OUTFILE}";
load "{CORE}";       
         
"""

GITIGNORE_wrapper_file=\
"""
*.aux
*.dvi
*.log
*.ps
*~
*.tex
**/fig.latex.nice/**
**/fig.tikz.nice/**
*converted*
plot_out.eps
"""




