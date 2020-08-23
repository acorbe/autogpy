
SHELL:=/bin/bash
latex_figs=$(wildcard *.pdflatex_compile.sh)
tikz_figs=$(wildcard *.tikz_compile.sh)
latex_targets_pdf=$(latex_figs:.pdflatex_compile.sh=.pdf)
tikz_targets_pdf=$(tikz_figs:.tikz_compile.sh=.tikz.pdf)
all_targets=$(latex_targets_pdf) $(tikz_targets_pdf)


all: $(latex_targets_pdf)
latex: $(latex_targets_pdf)
tikz:  $(tikz_targets_pdf)


%.tikz.pdf: %.tikz_compile.sh %.tikz.gnu %.core.gnu
	bash $<
	-[[ -f "compiled_files_redirection.string" ]] && (mkdir -p `cat compiled_files_redirection.string`)
	-[[ -f "compiled_files_redirection.string" ]] && (cp $@ `cat compiled_files_redirection.string`)


%.pdf: %.pdflatex_compile.sh %.pdflatex.gnu %.core.gnu
	bash $<
	-[[ -f "compiled_files_redirection.string" ]] && (mkdir -p `cat compiled_files_redirection.string`)
	-[[ -f "compiled_files_redirection.string" ]] && (cp $@ `cat compiled_files_redirection.string`)


clean:
	rm -f *.pdf *.jpg
	rm -Rf fig.latex.nice

deepclean:
	rm -rf *

.PHONY: sync
sync:
	bash sync_me.sh

