
mkdir -p fig.latex.nice
gnuplot fig__.pdflatex.gnu || exit 1

latex fig.latex.nice/plot_out.tex
dvips plot_out.dvi  -o plot_out.ps
ps2eps --ignoreBB -f plot_out.ps
ps2pdf plot_out.ps

mv plot_out.pdf fig__.pdf

if command -v pdftoppm &> /dev/null
then

    pdftoppm -png fig__.pdf > fig__.pdf_converted_to.png

else
## this step converts in png for displaying the image in jupyter
if convert -density 100 fig__.pdf -quality 100 fig__.pdf_converted_to.png 
then
  echo "conversion successful"
else
  echo ""
  echo "-ERROR: The convert command gave an error."
  echo "        This means that pdftoppm also gave an error or it is not installed."
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
