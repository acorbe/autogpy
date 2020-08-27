import autogpy
import numpy as np

XX_test_linspace = np.linspace(0,1,50)

def test_plot_1_arg_nparray():
    with autogpy.Figure("test_plot_1_arg_nparray",file_identifier="figtest") as fig:
        fig.plot(XX_test_linspace)

    fcontent = fig.get_gnuplot_file_content()

    # syntax needs generalization 
    assert 'p  "figtest__0__.dat"' in fcontent

    # we want a default title if none is passed such that the underscores do not mess up gnuplot
    assert 'title' in fcontent

def test_label_adds_string():
    with autogpy.Figure("test_plot",file_identifier="figtest") as fig:
        fig.plot(XX_test_linspace, label="foo")

    fcontent = fig.get_gnuplot_file_content()

    assert 'title "foo"' in fcontent

def test_title_kw_shorteners_string():
    title_shortners = ['title', 'titl', 'tit', 'ti', 't']

    for title_sh in title_shortners:
        with autogpy.Figure("test_plot",file_identifier="figtest") as fig:
            fig.plot(XX_test_linspace, label="foo")

        fcontent = fig.get_gnuplot_file_content()

        assert 'title "foo"' in fcontent

    
    
    
    
