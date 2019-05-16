# autogpy - AutoGnuplot.py
Automatic generation of gnuplot figures (including script and data) from python.

Author: [Alessandro Corbetta](http://corbetta.phys.tue.nl/), 2019



**Which problem does it solve?**

In the scientific community, [gnuplot](http://www.gnuplot.info/) is a gold standard for high-quality plots. It used across generations of scientists.  
Python is quickly becoming a tool of choice for data analytics. Although python comes with several options for plotting, often gnuplot is preferred in production.

`autogpy` eliminates annoying duplication of code/data between pyton analyses and gnuplot figure production.  
Using a syntax close to gnuplot, automatically generates gnuplot scripts and dumps suitably the data. 




## In a nutshell

### Installation

```bash
git clone git@github.com:acorbe/autogpy.git
pip install ./autogpy
```

### Usage

```python
import autogpy
import numpy as np

xx = np.linspace(0,6,100)
yy = np.sin(xx)
zz = np.cos(xx)

figure = autogpy.AutogpyFigure("test_figure","test1")

figure.p_generic(r'u 1:2 with lines t "sin"',xx,yy)
figure.p_generic(r'u 1:2 with lines t "cos"',xx,zz)
figure.generate_gnuplot_file()

figure.jupyter_show_pdflatex() # only in jupyter

```


will generate the following figure (also appearing in jupyter)

<img src="https://github.com/acorbe/autogpy/example_fig.jpeg" alt="example figure" width="500px" >


**Most importantly**, the following source and data will be created in the folder `test_figure` 

```bash
$ ls test_figure

Makefile
sync_me.sh
test1__0__.dat
test1__1__.dat
test1__.core.gnu
test1__.jpg.gnu
test1__.pdflatex_compile.sh
test1__.pdflatex.gnu
test1__.tikz_compile.sh
test1__.tikz.gnu
```

With `make` one can obtain jpg, epslatex, and tikz/pgfplot versions of the figure.
Notice that the input data has been formatted automatically.

Inspecting `test1__.pdflatex.gnu`, responsible of the epslatex version of the figure, one gets:
```gnuplot
set terminal epslatex size 9.9cm,8.cm color colortext standalone      'phv,12 '  linewidth 2
set output 'fig.latex.nice/plot_out.tex'

load "test1__.core.gnu"; 
```
while `test1__.core.gnu` reads:
```gnuplot
p "test1__0__.dat" u 1:2 with lines t "sin",\
"test1__1__.dat" u 1:2 with lines t "cos"

```


