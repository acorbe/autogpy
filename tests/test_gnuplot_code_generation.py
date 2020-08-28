import autogpy
import numpy as np
import re

XX_test_linspace = np.linspace(0, 1, 50)


def test_plot_1_arg_nparray():
    with autogpy.Figure("test_plot_1_arg_nparray",
                        file_identifier="figtest") as fig:
        fig.plot(XX_test_linspace)

    fcontent = fig.get_gnuplot_file_content()

    # syntax needs generalization
    assert 'p  "figtest__0__.dat"' in fcontent

    # we want a default title if none is passed such
    # that the underscores do not mess up gnuplot
    assert 'title' in fcontent


def test_label_adds_string():
    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.plot(XX_test_linspace, label="foo")

    fcontent = fig.get_gnuplot_file_content()

    assert 'title "foo"' in fcontent


def test_title_kw_shorteners_string():
    title_shortners = ['title', 'titl', 'tit', 'ti', 't']

    for title_sh in title_shortners:
        with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
            fig.plot(XX_test_linspace, **{title_sh: "foo"})

        fcontent = fig.get_gnuplot_file_content()

        assert 'title "foo"' in fcontent


def test_title_with_latex_brackets():
    latex_text = "$v^{A}$"
    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.plot(XX_test_linspace, label=latex_text)

    fcontent = fig.get_gnuplot_file_content()

    assert 'title "%s"' % latex_text in fcontent


def test_plot_generic_nonstring_argument_passed_as_string():
    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.plot(XX_test_linspace, test_arg="2")

    fcontent = fig.get_gnuplot_file_content()
    assert "test_arg 2" in fcontent


def test_plot_generic_nonstring_argument_passed_as_int():
    with autogpy.Figure("test_print()lot", file_identifier="figtest") as fig:
        fig.plot(XX_test_linspace, test_arg=2)

    fcontent = fig.get_gnuplot_file_content()
    assert "test_arg 2" in fcontent


def test_plot_generic_string_argument():
    """do not see real use-case, beyond title, which is escaped in other ways.
    """
    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.plot(XX_test_linspace, test_arg__s="2")

    fcontent = fig.get_gnuplot_file_content()
    assert 'test_arg "2"' in fcontent

    # note that here we pass the arg as int.
    # It should be casted as a string in the preocess
    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.plot(XX_test_linspace, s__test_arg=2)

    fcontent = fig.get_gnuplot_file_content()
    assert 'test_arg "2"' in fcontent


def test_title_with_latex_backslash():
    """backslash needs to be doubled to prevent escaping at the gnuplot
    level.
    """

    # note the raw string
    latex_text = r"$\lim_t v^{A}$"
    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.plot(XX_test_linspace, label=latex_text)

    fcontent = fig.get_gnuplot_file_content()

    assert 'title "%s"' % latex_text.replace("\\", "\\\\") in fcontent


def test_set_statement_one_args():

    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.set("key")
        fig.plot(XX_test_linspace)

    fcontent = fig.get_gnuplot_file_content()
    # print ("re output:", re.search(r"^\s*set key$", fcontent, re.MULTILINE))
    # print (fcontent)
    assert re.search(r"^\s*set key$", fcontent, re.MULTILINE)


def test_set_statement_multi_args():

    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.set("key", "grid")
        fig.plot(XX_test_linspace)

    fcontent = fig.get_gnuplot_file_content()
    # print ("re output:", re.search(r"^\s*set key$", fcontent, re.MULTILINE))
    # print (fcontent)
    assert re.search(r"^\s*set key$", fcontent, re.MULTILINE)
    assert re.search(r"^\s*set grid$", fcontent, re.MULTILINE)


def test_unset_statement_multi_args():

    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.unset("key", "grid")
        fig.plot(XX_test_linspace)

    fcontent = fig.get_gnuplot_file_content()
    # print ("re output:", re.search(r"^\s*set key$", fcontent, re.MULTILINE))
    # print (fcontent)
    assert re.search(r"^\s*unset key$", fcontent, re.MULTILINE)
    assert re.search(r"^\s*unset grid$", fcontent, re.MULTILINE)


def test_set_statement_one_kw():

    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.set(key="above")
        fig.plot(XX_test_linspace)

    fcontent = fig.get_gnuplot_file_content()
    # print ("re output:", re.search(r"^\s*set key above$"
    # , fcontent, # re.MULTILINE))
    # print (fcontent)
    assert re.search(r"^\s*set key above$", fcontent, re.MULTILINE)


def test_set_statement_multi_kw():

    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.set(key="above", xl="x")
        fig.plot(XX_test_linspace)

    fcontent = fig.get_gnuplot_file_content()

    assert re.search(r"^\s*set key above$", fcontent, re.MULTILINE)
    # this would not be a valid gnuplot syntex
    assert re.search(r"^\s*set xl x$", fcontent, re.MULTILINE)


def test_set_statement_string():

    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.set(xl__s="x")
        fig.plot(XX_test_linspace)

    fcontent = fig.get_gnuplot_file_content()
    # print(fcontent)
    assert re.search(r'^\s*set xl "x"$', fcontent, re.MULTILINE)

    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.set(s__xl="x")
        fig.plot(XX_test_linspace)

    fcontent = fig.get_gnuplot_file_content()
    # print(fcontent)
    assert re.search(r'^\s*set xl "x"$', fcontent, re.MULTILINE)


def test_set_statement_equation():

    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.set(xl__e="x")
        fig.plot(XX_test_linspace)

    fcontent = fig.get_gnuplot_file_content()
    # print(fcontent)
    assert re.search(r'^\s*set xl "\$x\$"$', fcontent, re.MULTILINE)

    with autogpy.Figure("test_plot", file_identifier="figtest") as fig:
        fig.set(e__xl="x")
        fig.plot(XX_test_linspace)

    fcontent = fig.get_gnuplot_file_content()
    # print(fcontent)
    assert re.search(r'^\s*set xl "\$x\$"$', fcontent, re.MULTILINE)
