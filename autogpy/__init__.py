"""autogpy - AutoGnuplot.py: generate gnuplot figures, with code and data, easily from python

.. moduleauthor:: Alessandro Corbetta <a.corbetta@tue.nl>

"""

from . import plot_helpers 
from .autognuplot import AutoGnuplotFigure

AutogpyFigure = AutoGnuplotFigure
Figure = AutoGnuplotFigure
AnonymousFigureF = lambda *args, **kw: AutoGnuplotFigure('.autogpy_anonymous_figure',
                                                         anonymous=True,
                                                         *args, **kw)
