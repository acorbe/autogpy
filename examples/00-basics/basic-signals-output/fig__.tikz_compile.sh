
mkdir -p fig.latex.nice
gnuplot fig__.tikz.gnu || exit 1

pdflatex fig.latex.nice/tikz_out.tex

mv tikz_out.pdf fig__.tikz.pdf

## check if pdftoppm exists, usually gives better results
if command -v pdftoppm &> /dev/null
then

    pdftoppm -png fig__.tikz.pdf > fig__.tikz.pdf_converted_to.jpg

else
if convert -density 100 fig__.tikz.pdf -quality 100 fig__.tikz.pdf_converted_to.jpg 
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
