<h1>autogpy - AutoGnuplot.py</h1>

<h2>Automatic generation of gnuplot figures/scripts/data from python.</h2>


**Author:** [Alessandro Corbetta](http://corbetta.phys.tue.nl/), 2019-2020   
**Documentation:** https://acorbe.github.io/autogpy/  
**Examples** [Link](https://github.com/acorbe/autogpy/tree/master/examples)  
**Github** [Link](https://github.com/acorbe/autogpy) 


[![PyPI](https://img.shields.io/pypi/v/autogpy)](https://pypi.org/project/autogpy/) [![build status](https://travis-ci.org/acorbe/autogpy.svg?branch=master)](https://travis-ci.org/github/acorbe/autogpy) [![Downloads](https://pepy.tech/badge/autogpy)](https://pepy.tech/project/autogpy)![PyPI - Downloads](https://img.shields.io/pypi/dm/autogpy)


### Which problem does it solve?

`autogpy` eliminates annoying duplications of code and data when employing python for data analysis and [gnuplot](http://www.gnuplot.info/) for figures. Providing a gnuplot-like or a matplotlib-like syntax, `autogpy` automatically generates gnuplot scripts and dumps suitably the data.  

![Autogpy-Demo](https://github.com/acorbe/autogpy/blob/master/doc/other/demo-animation.gif)

Links: [[Source](https://github.com/acorbe/autogpy/tree/master/examples/02-webexample/webmovie.ipynb)] [[Output](https://github.com/acorbe/autogpy/tree/master/examples/02-webexample/test-figure)]


### Main features
+ anything that be obtained by the gnuplot command `plot` can be produced
+ output figures are shipped in a folder which includes scripts, data and makefile
+ any gnuplot state modification can be achieved
+ terminals epslatex, tikz/pgfplot and jpg
+ multiplots
+ `plt.hist`-like gnuplot histogram figures generator
+ jupyter notebook figure preview
+ jupyter notebook gnuplot script inspection
+ easy scp-based synchronization between a machine in which the figures are generated (e.g. from even larger datasets) and the "paper writing" machine.

**Requirements**
+ Linux/MacOs (could work on Windows, yet it has not been adjusted for)
+ Python 3
+ Working latex distribution
+ Gnuplot, optionally with tikz terminal
+ `pdftoppm` (via [`poppler-utils`](https://command-not-found.com/pdftoppm)) or [`imagemagick`](https://command-not-found.com/convert) to convert the output pdf figures in png format for jupyter notebook preview 


### Getting autogpy

Via `pip`
```bash
pip install autogpy

```

On Google Colab
```bash
!apt install gnuplot texlive poppler-utils ghostscript texlive-latex-extra
!pip install autogpy
```

From source
```bash
git clone git@github.com:acorbe/autogpy.git
pip install autogpy/
```


## In a nutshell

Please see also the [examples](https://github.com/acorbe/autogpy/tree/master/examples) and the [documentation](https://acorbe.github.io/autogpy/).

```python
import autogpy
import numpy as np

xx = np.linspace(0,6,100)
yy = np.sin(xx)
zz = np.cos(xx)

with autogpy.AutogpyFigure("test_figure") as figure: 

	# gnuplot-like syntax
	figure.plot(r'with lines t "sin"',xx,yy)
	
	# matplotlib-like syntax
	figure.plot(xx,zz,u='1:2',w='lines',label='cos')
```

generates the following figure (also appearing in jupyter)

<img src="https://github.com/acorbe/autogpy/raw/master/example_fig.jpeg" alt="example figure" width="500px" >

**Most importantly**, the following source and data are created in the folder `test_figure` 

```bash
$ ls test_figure

.gitignore
Makefile
sync_me.sh
fig__0__.dat
fig__1__.dat
fig__.core.gnu
fig__.jpg.gnu
fig__.pdflatex_compile.sh
fig__.pdflatex.gnu
fig__.tikz_compile.sh
fig__.tikz.gnu
```

With `make` one can obtain jpg, epslatex, and tikz/pgfplot versions of the figure. Notice that the input data has been formatted automatically and dumped in the `.dat` files.

Inspecting the `fig__.pdflatex.gnu`, responsible of the epslatex version of the figure, one gets:
```gnuplot
set terminal epslatex size 9.9cm,8.cm color colortext standalone      'phv,12 '  linewidth 2
set output 'fig.latex.nice/plot_out.tex'

p "fig__0__.dat" with lines t "sin",\
"fig__1__.dat" u 1:2 with lines t "cos" 
```

**KWONW ISSUES**
+ Certain features require imagemagick and a working `gnuplot-tikz.lua`. Some versions of these might have bugs. Call `figure.display_fixes()` to show known fixes.

