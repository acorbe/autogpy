"""
This file is part of Autognuplotpy, autogpy.

"""
from __future__ import print_function

import os
import numpy as np
import warnings
from collections import OrderedDict
import re


from . import autognuplot_terms
from . import plot_helpers

try:
    import pandas as pd
    import pandas
    pandas_support_enabled = True
    # print("pandas support enabled")
except:
    pandas_support_enabled = False

warnings.simplefilter('once', UserWarning)

try:
    import pygments
    pygments_support_enabled = True
except:
    pygments_support_enabled = False


class AutoGnuplotFigure(object):
    """Creates an AutoGnuplotFigure object which wraps one gnuplot figure.


        Parameters
        ---------------------
        folder_name: str
             target location for the figure scripts and data
        file_identifier: str
             common identifier present in the file names of this figure object
        verbose: bool, optional
             (False) Verbose operating mode.
        autoescape: bool, optional
             (True) Autoescapes latex strings. It enables to use latex directly in raw strings without further escaping.
        latex_enabled: bool, optional
             (True) The Makefile of the generated figure will build a latex figure by default (in the first make statement)
        tikz_enabled: bool, optional
             (False) The Makefile of the generated figure will build a latex/tikz figure by default (in the first make statement). Disabled as the default tikz configuration has some issue. See method: `display_fixes`.
        hostname: str, optional
             (None) Allows to set an hostname different for the system one. This hostname is used for scp calls, so it should be changed to a reacheable hostname, if needed.
        jpg_convert_density: int, optional
             (100) dpi of the jpg image showed in a jupyter notebook. It is used for the conversion of the pdf image produced by gnuplot.
        jpg_convert_quality: int, optional
             (100) conversion quality of the jpg image showed in a jupyter notebook. It is used for the conversion of the pdf image produced by gnuplot.
        anonymous: bool, optional
             (False) Specifies if a figure is generated in an anonymous folder. (Options as ssh sync and latex inclusion are turned off).

        Returns
        --------------------
        fig : AutoGnuplotFigure


        Examples
        ----------------

        >>> # Usage case: no context manager, gnuplot syntax.
        >>> fig = AutoGnuplotFigure('folder','id')
        >>> # for some existing arrays x,y
        >>> fig.plot('u 1 : 2 t "my title" ', x ,y) 
        >>> fig.generate_gnuplot_file() 
        >>> # only jupyter
        >>> fig.jupyter_show_pdflatex(show_stdout=False) 

        Notes
        -----------------
        Setting latex terminal sizes. Change parameters in the member dictionary `pdflatex_terminal_parameters`

        >>> fig.pdflatex_terminal_parameters = 
        >>> {
        >>>     "x_size" : "9.9cm"
        >>>     , "y_size" : "8.cm"
        >>>     , "font" : "phv,12 "
        >>>     , "linewidth" : "2"
        >>>     , "other" : "" # use e.g. for header package import
        >>> }

    """

    def __init__(self
                 , folder_name
                 , file_identifier = "fig"
                 , verbose = False
                 , autoescape = True
                 , latex_enabled = True
                 , tikz_enabled = False
                 , allow_strings = False
                 , hostname = None
                 , jpg_convert_density = 100
                 , jpg_convert_quality = 100
                 , anonymous = False):
        """ Creates an AutoGnuplotFigure object

        :param folder_name: str
        :param file_identifier: str
        :param verbose: Bool
        :param autoescape: Bool
        :param latex_enabled: Bool
        :param tikz_enabled: Bool
        :param allow_strings: Bool
        :param hostname: str
        :oaran anonymous: Bool

        """
        
        self.verbose = verbose
        
        self.folder_name = folder_name
        self.global_dir_whole_path = os.getcwd() + '/' +  self.folder_name
        self.file_identifier = file_identifier

        if not os.path.exists(self.folder_name):
            os.makedirs(self.folder_name)
            if self.verbose:
                print("created folder:", self.folder_name)

        self.global_file_identifier = self.folder_name + '/' + self.file_identifier
        self.globalize_fname = lambda x : self.folder_name + '/' + x

        # will get name of user/host... This allows to create the scp copy script
        self.__hostname = hostname
        self.__establish_ssh_info(hostname=self.__hostname)
        
        self.__dataset_counter = 0 

        self.datasetstring_template = "__{DS_ID}__{SPECS}.dat"

        self.datasets_to_plot = [ [] ]
        self.alter_multiplot_state = [  []  ] #the first altering block can be just global variables
        
        self.multiplot_index = 0
        self.is_multiplot = False
        
        self.global_plotting_parameters = []


        self.pdflatex_jpg_convert_density = jpg_convert_density
        self.pdflatex_jpg_convert_quality = jpg_convert_quality
        
        self.pdflatex_terminal_parameters = {
            "x_size" : "9.9cm"
            , "y_size" : "8.cm"
            , "font" : "phv,12 "
            , "linewidth" : "2"
            , "other" : ""

        }
        self._autoescape = autoescape

        self.variables = OrderedDict()

        self.terminals_enabled_by_default = {
            'latex' :
            {'type' : 'latex', 'is_enabled' : latex_enabled
             , 'makefile_string' : '$(latex_targets_pdf)'}
            ,
            'tikz' : {'type' : 'tikz', 'is_enabled' : tikz_enabled
                      , 'makefile_string' : '$(tikz_targets_pdf)'}
        }

        
        
        self.__Makefile_replacement_dict = { 
            'TAB' : "\t"  #ensure correct tab formatting
            , 'ALL_TARGETS' : "" + " ".join(
                [ x['makefile_string'] for x in self.terminals_enabled_by_default.values() if x['is_enabled'] ]
            ) 
        }

        self._allow_strings = allow_strings 

        # initializes the Makefile and the autosync script
        with open( self.globalize_fname("Makefile"), "w" ) as f:
            f.write(  autognuplot_terms.MAKEFILE_LATEX.format(
                **self.__Makefile_replacement_dict
            )  )

        with open( self.globalize_fname("sync_me.sh"), "w" ) as f:
            f.write(  autognuplot_terms.SYNC_sc_template.format(
                SYNC_SCP_CALL = self.__scp_string_nofolder
            )
            )

        self.is_anonymous = anonymous

    def set_figure_size(self,x_size=None, y_size=None, **kw):
        """Sets the terminal figure size and possibly more terminal parameters (string expected).
        """
        if x_size is not None:
            self.pdflatex_terminal_parameters["x_size"] = x_size

        if y_size is not None:
            self.pdflatex_terminal_parameters["y_size"] = y_size

        self.pdflatex_terminal_parameters.update(**kw)

    def set_figure_linewidth(self,lw):
        """Sets the global linewidth parameter for latex/tikz figures."""
        self.pdflatex_terminal_parameters.update({'linewidth' : lw})

    def __wrap_text_section(self,content,wrapper):

        repl = dict(WRP=wrapper, CONTENT=content)
        content.insert(0,"# BEGIN {WRP}".format(**repl) )
        content.append("# END {WRP}".format(**repl))
        
        return content

    def extend_global_plotting_parameters(self, *args, **kw):
        """Extends the preamble of the gnuplot script to modify the plotting settings. 
        
        Expects one or more strings with gnuplot syntax.

        Parameters
        ---------

        *args: strings
              Set the global gnuplot state for properties such as axis style, legend position and so on.
              Use gnuplot syntax. Raw strings are advised.

        autoescape: bool, optional
              Avoids escaping latex strings. Latex source can be written as is.

        Returns
        --------------
        fig : AutoGnuplotFigure

        

        Examples
        -----------
        >>> figure.extend_global_plotting_parameters(
        >>> r'''
        >>> set mxtics 2
        >>> set mytics 1
        >>> #
        >>> # color definitions
        >>> set border linewidth 1.5
        >>> set style line 1 lc rgb '#ff0000'  lt 1 lw 2
        >>> set style line 2 lc rgb '#0000ff' lt 3 lw 4
        >>> #
        >>> # Axes
        >>> set style line 11  lc rgb '#100100100' lt 1
        >>> set border 3 back ls 11
        >>> set tics nomirror out scale 0.75
        >>> #
        >>> # Grid
        >>> set style line 12 lc rgb'#808080' lt 0 lw 1
        >>> set grid back ls 12
        >>> #
        >>> set format y '$%.4f$'
        >>> set format x '$%.4f$'
        >>> #
        >>> set key top left
        >>> #
        >>> set key samplen 2 inside spacing 1 width 0.3 height 1.5  at graph 0.99, 1.05
        >>> #
        >>> unset grid
        >>> #set logscale y
        >>> set xlabel "$\\nu$"
        >>> set xrange [1e-5:1.05e-3]
        >>> set yrange [1e-5:1e-3]
        >>> set xtics 0,2e-4,1.01e-3
        >>> #set ytics 2e-4,2e-4,1.01e-3
        >>> ''')        

        """
        autoescape = kw.get("autoescape", self._autoescape)
        final_content = []
        if autoescape:
            for idx,a in enumerate(args):
                final_content.append(self.__autoescape_strings(a))            
        else:
            final_content = args

        self.global_plotting_parameters.extend(
            self.__wrap_text_section(final_content, "parameters"))
        
        return self

    def set_parameters(self,*args,**kw):
        """Proxies extend_global_plotting_parameters
        """
        return self.alter_current_multiplot_parameters(*args,**kw)

    def set(self,*args,**kw):
        """expands to preamble param in each subplot, prepends the set command
        """

        add_set_statement = lambda x : "set " + x
        if len(args):
            args_with_set_in_front = [add_set_statement(str(x)) for x in args]
            args_with_set_in_front_txt = "\n".join(args_with_set_in_front)
        else:
            args_with_set_in_front_txt = ""
            

        ## never needs autoescaping. The args branches is easy.
        self.set_parameters(args_with_set_in_front_txt)
        
        ## for some arguments autoescape is applied by self.__v_in_kw_needs_string, we should not apply it twice.
        if len(kw):
            kw_with_set_in_front = []
            for k,v in kw.items():
                k,v = self.__v_in_kw_needs_string(k,v)
                self.set_parameters("set " + str(k) + " " + str(v), autoescape = False)
                
        #         kw_with_set_in_front.append("set " + str(k) + " " + str(v))
        #     kw_with_set_in_front_txt = "\n".join(kw_with_set_in_front)            
        # else:
        #     kw_with_set_in_front_txt = ""
        # self.set_parameters(args_with_set_in_front_txt,kw_with_set_in_front_txt)


    def unset(self,*args,**kw):
        """expands to preamble param in each subplot, prepends the unset command. For the kws the argument is ignored.
        """

        add_set_statement = lambda x : "unset " + x
        if len(args):
            args_with_set_in_front = [add_set_statement(str(x)) for x in args]
            args_with_set_in_front_txt = "\n".join(args_with_set_in_front)
        else:
            args_with_set_in_front_txt = ""

        if len(kw):
            kw_with_set_in_front = []
            for k,v in kw.items():
                k,v = self.__v_in_kw_needs_string(k,v)
                kw_with_set_in_front.append("unset " + str(k))

            kw_with_set_in_front_txt = "\n".join(kw_with_set_in_front)
            
        else:
            kw_with_set_in_front_txt = ""

        self.set_parameters(args_with_set_in_front_txt,kw_with_set_in_front_txt)        

        
    def __v_in_kw_needs_string(self,k,v):
        """determines wheter v needs to be wrapped in quotes ("<v>") or in dollars and quotes ("$<v>$").

        prepending `s__` or appending `__s` to `k` yields stringification;  
        prepending `s__` or appending `__s` to `k` yields stringification and wrapping in `$` signs.
        """
        if k.startswith('s__') \
           or k.endswith('__s'):
            # or k.startswith('str__') \
            # or k.startswith('__str') \
            # or k.startswith('S__') \
            # or k.endswith('__S'):
                        
            needs_string = True
            # maybe it was not a string, but we asked for a string.
            v = str(v)
            k = k.replace('s__','').replace('__s','')
            
        elif k.startswith('e__') \
           or k.endswith('__e'):

            needs_string = True
            # maybe it was not a string, but we asked for a string.
            v = "$" + str(v) + "$"  
            k = k.replace('e__','').replace('__e','')
            
        else:
            needs_string = False

        if needs_string:
            new_v = self.__autoescape_if_string(v
                                                , add_quotes_if_necessary=True
                                                # in this case we expect not to perform
                                                # any string.format operation,
                                                # thus we avoid to double curly brackets
                                                , double_curly_brackets=False)
            # print(new_v)
            return k, new_v
        else:
            return k,str(v)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.generate_gnuplot_file()        
        try:
            from IPython.display import display, HTML
            get_ipython
            if self.terminals_enabled_by_default['tikz']['is_enabled']:
                self.jupyter_show_tikz()
            else:
                self.jupyter_show_pdflatex()
        except:
            pass


    def set_multiplot(self, specifiers = ""):
        """Enables multiplot mode (use in combination with `next_multiplot_group`). 
        
           
        Parameters
        --------------
        specifiers: str
             multiplot parameters. E.g. argument "layout 2,2" yields a 2x2 matrix 

        
        Returns
        --------------
        fig : AutoGnuplotFigure

        See also
        ------------
        next_multiplot_group, alter_current_multiplot_parameters

        
        Example
        -------------
        >>> # establishes multiplot mode with 2 rows and one column
        >>> fig.set_multiplot("layout 2,1") 
        >>> #plot in position 1,1
        >>> fig.p_generic('u 1 : 2 t "my title" ', x ,y) 
        >>> #next item in multiplot
        >>> fig.next_multiplot_group() 
        >>> #plot in position 2,1
        >>> fig.p_generic('u 1 : 2 t "my title" ', x ,z) 
        
        """
        
        self.is_multiplot = True
        self.extend_global_plotting_parameters(
            "set multiplot " + specifiers
        )

        return self

    def next_multiplot_group(self):
        """Shifts the state to the next plot in the multiplot sequence.

        Returns
        --------------
        fig : AutoGnuplotFigure

        See also
        -------------
        set_multiplot, alter_current_multiplot_parameters
        
        """
        
        if not self.is_multiplot:
            raise Exception("set_multiplot() is expected to use this feature")
        self.multiplot_index += 1
        self.datasets_to_plot.append([])
        self.alter_multiplot_state.append([])

        return self

    def alter_current_multiplot_parameters(self,*args,**kw):
        """Allows to change state variables of current subplot. 

        Works similarly to `extend_global_plotting_parameters`, but allows selective changes between one subplot and the next

        Parameters
        ------------------------
        *args: strings
              Set the global gnuplot state for properties such as axis style, legend position and so on.
              Use gnuplot syntax. Raw strings are advised.

        autoescape: bool, optional
              Avoids escaping latex strings. Latex source can be written as is.


        Returns
        --------------
        fig : AutoGnuplotFigure

        See also
        ---------------
        extend_global_plotting_parameters,set_multiplot,next_multiplot_group


        Examples
        ------------------        
        >>> # establishes multiplot mode with 2 rows and one column 
        >>> fig.set_multiplot("layout 2,1") 
        >>> #sets logscale in y, globally
        >>> fig.extend_global_plotting_parameters(r"set logscale y") 
        >>> #sets xrange, globally
        >>> fig.extend_global_plotting_parameters(r"set xrange [1e-5:1.05e-3]")
        >>> #plot in position 1,1
        >>> fig.p_generic('u 1 : 2 t "my title" ', x ,y) 
        >>> #next item in multiplot
        >>> fig.next_multiplot_group() 
        >>> ### to change xrange from second subplot onwards
        >>> fig.alter_current_multiplot_parameters(r"set xrange [1e-7:1.05e-2]")  
        >>> #plot in position 2,1
        >>> fig.p_generic('u 1 : 2 t "my title" ', x ,z) 

        For inset plots

        >>> fig.set_multiplot()
        >>> #sets logscale in y, globally
        >>> fig.extend_global_plotting_parameters(r"set logscale y") 
        >>> #sets xrange, globally
        >>> fig.extend_global_plotting_parameters(r"set xrange [1e-5:1.05e-3]") 
        >>> #plot in position 1,1
        >>> fig.p_generic('u 1 : 2 t "my title" ', x ,y) 
        >>> #next item in multiplot
        >>> fig.next_multiplot_group()
        >>> fig.alter_current_multiplot_parameters(
        >>> r\"\"\"set size 0.6, 0.5
        >>> # set size of inset
        >>> set origin 0.4, 0.5
        >>> # move bottom left corner of inset
        >>> \"\"\")
        >>> #inset plot
        >>> fig.p_generic('u 1 : 2 t "my title" ', x ,z)        
        """
        
        autoescape = kw.get("autoescape", self._autoescape)
        escaped_args = []
        if autoescape:
            for idx,a in enumerate(args):
                escaped_args.append(self.__autoescape_strings(a))
            self.alter_multiplot_state[self.multiplot_index].extend(escaped_args)            
        else:
            self.alter_multiplot_state[self.multiplot_index].extend(args)

        return self

    def set_multiplot_parameters(self,*args,**kw):
        """Proxies alter_current_multiplot_parameters
        """
        self.alter_current_multiplot_parameters(*args,**kw)
        
    
    def load_gnuplotting_palette(self, palette_name):
        """Downloads a color palette https://github.com/Gnuplotting/gnuplot-palettes and return the loading string to be added in the preamble of the plot (see example).

        Parameters
        ------------------------
        palette_name: string
            name of the palette, e.g. 'moreland'

        Returns
        -----------------------
        string 

        Example
        ----------------------
        >>> # Loads moreland palette in the current figure
        >>> fig.extend_global_plotting_parameters ( fig.load_gnuplotting_palette('moreland') )
        >>> # colors need to be selected manually        
        
        """
        return plot_helpers.load_gnuplotting_palette(palette_name, self.folder_name)

    def __get_multiplot_current_dataset(self):
        return self.datasets_to_plot[self.multiplot_index]

    def __append_to_multiplot_current_dataset(self, x):
        self.datasets_to_plot[self.multiplot_index].append(x)
    

    def add_xy_dataset(self
                       , x
                       , y                       
                       , gnuplot_opt = ""
                       , fname_specs = ""
    ):
        """Deprecated: Makes a x-y plot. Use `plot` instead.
        """

        x = np.array(x)
        y = np.array(y)
        data = np.concatenate([x[:,np.newaxis] ,y[:,np.newaxis]  ],axis = 1)
        dataset_fname = self.file_identifier + self.datasetstring_template.format(            
            DS_ID = self.__dataset_counter
            , SPECS = fname_specs)
        
        np.savetxt( self.globalize_fname(dataset_fname) ,  data)

        
        self.__append_to_multiplot_current_dataset(
            {'dataset_fname' : dataset_fname
             , 'plottype' : 'xy'
             , 'gnuplot_opt' : gnuplot_opt
             , 'gnuplot_command_template' : """ "{DS_FNAME}" u 1:2 {OPTS}  """

            }

        )
        self.__dataset_counter += 1


    def __hist_normalization_function(self
                                      , v_
                                      , normalization ):

        N_coeff = 1
        if normalization is not None:
            if isinstance( normalization, float):
                N_coeff =  normalization
            elif isinstance( normalization, str):
                if normalization == 'max':
                    N_coeff = np.max(v_)
        

        return N_coeff 

        

    def hist_generic(self, x
                     , gnuplot_command_no_u
                     , hist_kw = {}
                     , gnuplot_command_using = "u 1:2"
                     , normalization = None
                     , kde = False
                     , kde_kw = {}
                     , reweight = lambda edges_mid : 1
                     , dump_data = False
                     , compress_dumped_data = True
                     , **kw
                    ):

        """Proxy function to generate histograms 

        Parameters
        ------------------------
        x: list, np.array, or other format compatible with np.histogram
             1D dataset to histogram
        gnuplot_command_no_u: str
             gnuplot `plot` call arguments, skipping the filename and the `usigng` part. Should be used for title, plotstyle, etc.
        hist_kw: dict, optional
             ({}) arguments to pass to the inner np.histogram call
        gnuplot_command_using: str, optional
             ("u 1:2") overrides the default `using` part. (default: "using 1:2")
        normalization: float, str, optional
             (None) allows to provide a further normalization coefficient (pass float) or to normalize such that the `max` is one (pass `'max'`)
        kde: bool, optional
             (False) a gaussian kernel will be used to histogram the data, edges used are from the np.histogram call. 
             Note the number of bins is specified in the hist_kw dict.
        kde_kw: dict, optional
             ({}) parameters to pass to the `scipy.stats.gaussian_kde` call
        reweight: function, optional
             (`lambda: edges_mid : 1`) function to reweight the histogram or kde values. Receives the bin center as parameter.
        dump_data: bool, optional
             (False) dumps the input data as csv
        compress_dumped_data: bool, optional
             (True) the data dumped (by dump_data = True) are gz-compressed.
        **kw: optional
             passes through to the inner `p_generic` call.

        Returns
        ------------
        p_generic output
        """

        v_, e_ = np.histogram(x,**hist_kw)
        edges_mid = .5 * (e_[1:] + e_[:-1])
        
        
        if kde:
            from scipy.stats import gaussian_kde
            kernel = gaussian_kde(x,**kde_kw)

            kde_vals = kernel(edges_mid)

            v_ = kde_vals        
            
        v_ = v_ * reweight(edges_mid)                   

        N_coeff = self.__hist_normalization_function(v_,normalization)
        # if self.verbose:
        #     print("v_:", v_)
        #     print("N_coeff:", N_coeff)
        v_ = v_ / N_coeff

        plot_out = self.p_generic(
            gnuplot_command_using + " " + gnuplot_command_no_u
            , edges_mid , v_
            , **kw
        )
        if dump_data:
            if self.verbose:
                print("Dumping histogram raw data.")
            dataset_fname_hist = plot_out["dataset_fname"]
            dataset_dump_data = dataset_fname_hist + '.hist_compl_dump.dat' + ( '.gz' if compress_dumped_data else '' )
            globalized_dataset_dump_data = self.globalize_fname(dataset_dump_data)

            xyzt = [  x[: , np.newaxis ] if len(x.shape) == 1 else x for x in [x] ]                   
                    
            data = np.concatenate( xyzt , axis = 1 )
            np.savetxt( globalized_dataset_dump_data ,  data)
                    
        return plot_out

    def hist_plthist(self
                     , x
                     , normalization = None
                     , gnuplot_command_no_u_no_title = ''
                     , title=''                     
                     , suppress_plt_figure = True
                     , **kw):
        """Histogram function. Proxies the interface of plt.hist for a rapid call swap. 

        Arguments
        ----------
        x: list, array
             1D array to histogram
        normalization: float, str, optional
             (None) renormalizes the data after the historgram (see `hist_generic`)
        gnuplot_command_no_u_no_title: str, optional
             ('') additional gnuplot commands, excluding title
        title: str, optional
             ('') gnuplot `title`
        suppress_plt_figure: bool, optional
             (True) prevents the inner `plt.hist` call to spawn an histogram figure
        **kw: 
             `plt.hist` parameters
        
        """

        import matplotlib.pyplot as plt

        v_,e_,patches = plt.hist(x,**kw)
        if suppress_plt_figure:
            plt.close()

        edges_mid = .5 * (e_[1:] + e_[:-1])

        N_coeff = self.__hist_normalization_function(v_,normalization)
        v_ /= N_coeff
        
        self.p_generic(
            "u 1:2 t \"{TITLE}\" {REST}".format(TITLE = title
                                            , REST = gnuplot_command_no_u_no_title) 
            , edges_mid , v_            
        )        
        
        
    def __autoescape_strings(self, command_line, double_curly_brackets=True):
        """autoescapes backslashes. Additionally, by default doubles the the curly brackets, to prevent them to disturb the a forthcoming string.format call.
        """
        command_line = command_line.replace("\\","\\\\")
        if double_curly_brackets:
            command_line = command_line.replace("{","{{")
            command_line = command_line.replace("}","}}")

        #preserves some needed blocks
        command_line = command_line.replace("{{DS_FNAME}}","{DS_FNAME}" )
        return command_line

    def __quote_argument(self, v):
        return '"%s"' % str(v)

    def __autoescape_if_string(self
                               , el
                               , add_quotes_if_necessary = False
                               , double_curly_brackets = True):
        if isinstance(el,str):
            escaped_str = self.__autoescape_strings(el
                                                    , double_curly_brackets = double_curly_brackets)
            if add_quotes_if_necessary:
                return self.__quote_argument(escaped_str)
            else:
                return escaped_str
            # Q = '"' if add_quotes_if_necessary else ""
            # return '{Q}{CONTENT}{Q}'.format(CONTENT=escaped_str,Q=Q)
        else:
            return str(el)

    def __p_generic_kw_expansion(self,command_line,dataset_fname,kw_reserved,kw):
        ### title assessment part
        # 1. checks if it is in command line else
        #   2. if label is provided  (as matplotlib) keeps else
        #      3. if creates it from filename


        ### command forwarding part
        ## the negative logic has less exceptions
        # kw_forward = ["ls", "ps", "lw","w"]
        # for k,v in kw.items():
        #     if k in kw_forward:
        #         command_line = command_line + " " + k + " " + str(kw[k])

        for k,v in kw.items():
            if not k in kw_reserved:
                ## to replace with function __v_in_kw_needs_string
                # if k.startswith('s__') \
                #    or k.endswith('__s'):                        
                #     needs_string = True
                #     # maybe it was not a string, but we asked for a string.
                #     v = str(v)
                #     k = k.replace('s__','').replace('__s','')
                # else:
                #     needs_string = False
                k,v = self.__v_in_kw_needs_string(k,v)

                command_line = command_line + " " \
                    + k + " "\
                    + v #self.__autoescape_if_string(v, add_quotes_if_necessary = needs_string)
                                

        ## needs to go after the blind adding to the command line,
        ## as this one only highjacks the title
        user_defined_title = False
        if 'label' in kw:
            user_defined_title = True
            if isinstance(kw['label'],str):                    
                title_guess = self.__autoescape_strings(kw['label'])
            else:
                title_guess = str(kw['label'])
                    
        else:
            ## two underscores reads bad, we just put one.
            if dataset_fname is not None:
                title_guess = dataset_fname.split('/')[-1].replace("__","_").replace("_","\\\_")
            else:
                title_guess = None
                
        if " t " not in command_line \
           and " t\"" not in command_line\
           and " title " not in command_line\
           and " title\"" not in command_line\
           and title_guess is not None:

            command_line =  command_line + " " + """title "{TITLE}" """.format(TITLE = title_guess)
            
            if self.verbose and not user_defined_title:
                print('Warning: a title will be appended to avoid latex compilation problems')
                print('the final command reads:')
                print(command_line)


        return {'title_guess' : title_guess
                , 'command_line' : command_line}

        
    
    def plot(self, command_line_or_data, *args, **kw):
        """Central plotting primitive.
                
        Arguments
        ----------
        command_line_or_data: string, list, `np.array` or `pd.Series`
             gnuplot command, without the explicit call to plot and the filename of the content.
             Alternatively, can be a list or np.array containing data (see *args)
        *args: lists or np.array, optional
             columns with the data, one or more columns can contain strings (e.g. for labels). In this case 'allow_strings' must be True.
        fname_specs: string, optional
             ("") allows to specify a filename for the data different for the default one.
        autoescape: bool, optional
             (as set in by the constructor) allows to selectively modify the class setting for autoescaping.
        allow_strings: bool, optional
             (False) set to True to allows columns with strings. This requires pandas. Might become True by default in the future.
        column_names: list of strings, optional
             (None) set the names of the columns. Considered only if `allow_strings=True`.
        `for_`: string, optional
             (None) allows to use the `for` gnuplot keyword.
        label: string, optional
             (None) proxies the gnuplot `title` keyword.
        **generic_gnuplot_command: kw and value, optional
             ({}) allows to pass any gnuplot argument ex `ls`, `linewidth`, etc.

        """
        # aliasing the variable, the rest of the code considers the old naming
        command_line = command_line_or_data
        
        fname_specs = kw.get("fname_specs","")
        autoescape = kw.get("autoescape",self._autoescape)
        allow_strings = kw.get("allow_strings",self._allow_strings)
        column_names = kw.get("column_names",None)
        for_enabled = kw.get("for_",None)        
        if for_enabled is not None:
            allow_strings = False
            for_prepend = "for " + for_enabled
        else:
            for_prepend = ""


        ## auto-wrapping the title with a string allowing to use t, ti, tit, titl, title kws.
        # true if a title is provided for the plot, it any form
        title_kw_provided = 'label' in kw

        title_kw = 'title'
        if not title_kw_provided:
            for idx in range(len(title_kw)):
                title_kw_attempt = kw.get(title_kw[0:idx+1],False)
                if title_kw_attempt is not False:
                    title_kw_provided = True
                    kw['label'] = title_kw_attempt
                    break

        ## the following keywords are not blindly appended to the command line
        kw_reserved = ["fname_specs", "autoescape", "allow_strings"
                       , "column_names", "for_", "label"
                       , "t", "ti", "tit", "titl", "title"]


        ### allowing to plot even without the command_line arg
        if not isinstance(command_line, str): # \
           #or isinstance(command_line, np.ndarray):
            #prepending 'command_line', which should now contain data

            args = command_line,*args            
            command_line = ''

        # autosupport for pandas series
        if pandas_support_enabled:
            if len(args) == 1: #pd.core.series.Series
                if isinstance(args[0],pandas.core.series.Series):
                    series = args[0]
                    args = series.index, series.values
                    if not title_kw_provided:
                        kw['label'] = str(series.name).replace("_"," ")
                        title_kw_provided = True


        if autoescape:
            command_line = self.__autoescape_strings(command_line)

            if self.verbose:
                print("autoescaping -- processing:", command_line)

        if len(args) == 0: #case an explicit function is plotted:
            dataset_fname = None
            kw_expansion_ret = self.__p_generic_kw_expansion(command_line,dataset_fname,kw_reserved,kw)
            command_line = kw_expansion_ret['command_line']
            
            to_append = \
                {'dataset_fname' : ""
                 , 'plottype' : 'expl_f'
                 , 'gnuplot_opt' : ""
                 ## initial spaces enable nice alignment
                 , 'gnuplot_command_template' : "  " + command_line 
                 #, 'prepended_parameters' : prepend_parameters
                }
            
            self.__append_to_multiplot_current_dataset(
                to_append 
            )            
        else:

            dataset_fname = self.file_identifier + self.datasetstring_template.format(            
                DS_ID = self.__dataset_counter
                , SPECS = fname_specs)

            globalized_dataset_fname = self.globalize_fname(dataset_fname)

            if allow_strings and pandas_support_enabled:
                # pandas way. need to import
                import pandas as pd
                if column_names is None:
                    column_names = ["col_%02d" % x for x in range(len(args))]
                    
                xyzt = pd.DataFrame(
                    {
                        n : v
                        for n,v in zip(column_names, args)
                    }
                )
                xyzt.to_csv(globalized_dataset_fname
                            , sep = " "
                            , header = False
                            , index = False)
                if self.verbose:
                    print(xyzt)

                ##########
            else:
                # numpy way
                try:
                    xyzt = list(map( lambda x : np.array(x), args  ))
                    ## adding second dimension if needed, this is a feature to allow a for loop
                    xyzt = [  x[: , np.newaxis ] if len(x.shape) == 1 else x for x in xyzt]                   
                    
                    data = np.concatenate( xyzt , axis = 1 )
                    np.savetxt( globalized_dataset_fname ,  data)
                except TypeError:
                    print("\nWARNING: You got this exception likely beacuse you have columns with strings.\n"
                          "Please set 'allow_strings' to True.")
                    raise

            if '"{DS_FNAME}"' not in command_line:
                if self.verbose:
                    print('[%s] Warning: "{DS_FNAME}" will be prepended to your string' % command_line)
                command_line = for_prepend + ' "{DS_FNAME}"' + " " + command_line

            kw_expansion_ret = self.__p_generic_kw_expansion(command_line,dataset_fname,kw_reserved,kw)            

            command_line = kw_expansion_ret['command_line']

            to_append = {
                'dataset_fname' : dataset_fname
                 , 'plottype' : 'xyzt_gen'
                 , 'gnuplot_opt' : ""
                 , 'gnuplot_command_template' : command_line
                 #, 'prepended_parameters' : prepend_parameters
                }

            self.__append_to_multiplot_current_dataset(
                to_append
            )
            self.__dataset_counter += 1

        return to_append

    def get_txt_dataset(self,ds_path):
        """loads a txt dataset (proxies `np.loadtxt`)
        """
        ds = np.loadtxt(ds_path)
        return ds
    
        
    def p_generic(self, command_line, *args, **kw):
        """Proxies plot for backwards compatibility.
        """
        return self.plot(command_line,*args,**kw)

    def fit(self,foo, *args,**kw):
        """Fitting method from gnuplot.

        Arguments
        -------------------------
        foo: str
             name of the function to fit (must be defined in set parameters)
             if foo contains an `=` (as e.g. in `foo = "f(x)=a*x+b"), the function definition is automatically 
             included in the preamble. Note everthing after `=` is ported. 
             so far parses only scalar functions, like "`f(yy)=tt*yy`"

        modfiers: str
             ('auto_via') modifiers to the call, suited to include, e.g. the `via` specifier.
             if `'auto'` the `via` parameter is inferred. [experimental]

        *args: `list` or `np.array`
             data to fit

        do_not_fit: str or list(str)
             when inferring which parameters to fit, those in `do_not_fit` are excluded

        unicize_parameter_names: bool
             (False) if `True`, the inferred parameter names are renamed to be unique. 
             Experimental and buggy!
        
        """

        if isinstance(args[0], str):
            # the first argument is a modifier, need to add it to kw
            kw["modifiers"] = args[0]
            args = args[1:]
        else:
            # we need default condition on modifiers
            kw["modifiers"] = kw.get("modifiers","auto_via")

        modifiers = kw["modifiers"]
        if self.verbose:
            print("modifiers=",modifiers)
            
        do_not_fit_list = kw.get("do_not_fit",[])
        if isinstance(do_not_fit_list,str):
            do_not_fit_list = [do_not_fit_list]

        unicize_parameter_names = kw.get("unicize_parameter_names",False)

        # inferring the function syntax from 'foo'
        if '=' in foo:
            #we have a function definition here. Must be ported to the parameters
            _any_f_name="[a-zA-z][a-zA-z0-9_]*"
            _capture = lambda x : "(" + x + ")"

            __function_definition_block_regex = "^.*?\s*" + _capture( _any_f_name + "\(.+\)\s*=.*" )
            # 1. we extract the function definition block
            foo_def_block_r = re.search(__function_definition_block_regex,foo)
            foo_def_block_content = foo_def_block_r.group(1)


            # 3. we strip the variable foo from the function definition, as required by gnuplot
            foo = foo.split("=")[0]

            # 4. we parse the function definition
            __function_parts_regex = _capture( _any_f_name ) + "\s*\(" + _capture( _any_f_name ) + "\s*\)" + "\s*=.*"
            __function_parts_r = re.search(__function_parts_regex, foo_def_block_content)
            # 5. we extract the independent variables name
            foo_function_name = __function_parts_r.group(1)
            foo_independent_var_name = __function_parts_r.group(2)

            do_not_fit_list.append(foo_independent_var_name)

            print("[fit] inferred function name:", foo_function_name)
            print("[fit] inferred independent variable name:", foo_independent_var_name)
            print("[fit] names not for fitting", do_not_fit_list)

           
            if pygments_support_enabled and "auto_via" in modifiers:
                if self.verbose:
                    print("auto_via in modifiers, will proceed to infer the parameters to from the function definition")
                from pygments.lexers import GnuplotLexer
                from pygments.token import Token

                inferred_parameter_names_to_fit = []                
                loc_lexer = GnuplotLexer()

                found_equal_token = False
                for ch_idx, tk_type, val in loc_lexer.get_tokens_unprocessed(foo_def_block_content):
                    # if self.verbose:                    
                    #     print(type(tk_type), ch_idx, tk_type, val)

                    if found_equal_token and tk_type is Token.Name:
                        if val not in do_not_fit_list: # != foo_independent_var_name:
                            inferred_parameter_names_to_fit.append(val)

                    if not found_equal_token and tk_type is Token.Operator and val == "=":
                        # if self.verbose:
                        #     print("matched =")

                        found_equal_token = True

                print("[fit] inferred parameters to fit", inferred_parameter_names_to_fit)                
                modifiers = modifiers.replace("auto_via", "via " + ",".join(inferred_parameter_names_to_fit))
                
            if unicize_parameter_names:
                print("this feature is experimental and buggy")
                import uuid
                this_unique_name = "__" + str(uuid.uuid4().hex[:8])

                for vname in inferred_parameter_names_to_fit:
                    print(vname)
                    modifiers = modifiers.replace(vname,vname+this_unique_name)
                    foo_def_block_content = foo_def_block_content.replace(vname,vname+this_unique_name)
            else:
                this_unique_name = ""

            # 2b. we add the function definition to the preamble
            # print(foo_def_block_r.group(1))
            self.set_parameters(foo_def_block_content)

            # tentative for multiple arguments
            # TODO: this regex has a bug: it does not capture intermediate
            # variable arguments between the first and the last
            # re.search("^.*?\s*([a-zA-z][a-zA-z0-9_]*)\(([a-zA-z][a-zA-z0-9_]*)"
            #           "(,[a-zA-z][a-zA-z0-9_]*?)*\)=(.*)", )


        dataset_fname = self.file_identifier + self.datasetstring_template.format(            
                DS_ID = self.__dataset_counter
                , SPECS = "fit")

        globalized_dataset_fname = self.globalize_fname(dataset_fname)

        # this part needs to be refactored outputs
        xyzt = list(map( lambda x : np.array(x), args  ))
        # adding second dimension if needed, this is a feature to allow a for loop
        xyzt = [  x[: , np.newaxis ] if len(x.shape) == 1 else x for x in xyzt]                   
        
        data = np.concatenate( xyzt , axis = 1 )
        np.savetxt( globalized_dataset_fname ,  data)
        
        
        to_append = {"dataset_fname" : dataset_fname
                     , "plottype" : "gnuplotfit"
                     , "gnuplot_opt" : ""
                     , 'gnuplot_command_template' : '{FOO} "{{DS_FNAME}}" {MODS}'.format(FOO = foo, MODS=modifiers) }
        
        self.__append_to_multiplot_current_dataset(
                to_append
        )
        self.__dataset_counter += 1
    

    def fplot(self,foo,xsampling=None,
              xsampling_N=100,
              **kw):
        """Mimicks matlab fplot function. 

        Matlab ref: https://www.mathworks.com/help/matlab/ref/fplot.html

        Parameters
        ----------------
        foo: scalar function
            foo(n) must be evaluable.

        xsampling: iterable, optional
            (`np.linspace(-5,5)`) contains the x samples on which foo is evaluated.

        **kw: same as in `plot`        
        """

        if xsampling is None:
            xsampling = np.linspace(-5,5,xsampling_N)
        elif isinstance(xsampling,tuple):
            xsampling = np.linspace(xsampling[0],xsampling[1],xsampling_N)

        yval = [foo(x) for x in xsampling]

        return self.plot(xsampling,yval,**kw)

    
    def add_variable_declaration(self,name,value,is_string = False):
        """Add functions and variables declaration in the script preamble.

        Parameters
        ------------------------
        name: string
            Variable or function name. In case of a function needs to read like `"f(x)"`
        value: value or string

        is_string: bool, optional
            (False) If `True` wraps value in double-quote signs. 
        
        """
        self.variables[name] = '"%s"'%str(value) if is_string else str(value)
        

    def __render_variables(self):

        return "\n".join(
            [ "{NAME}={VALUE}".format(NAME = k, VALUE=v) for (k,v) in self.variables.items()    ]
        )
        
        
    def __generate_gnuplot_plotting_calls(self):
        calls = []
        mp_count = 0
        for alterations, datasets in zip(self.alter_multiplot_state
                                        , self.datasets_to_plot):
            
            alterations_t = "\n".join( ["\n# this is multiplot idx: %d" % mp_count] + alterations + [""])

            datasets_for_fit = filter( lambda x : x['plottype'] in ['gnuplotfit'], datasets )

            
            fit_call = "\n".join(
                [ "fit " + x[ 'gnuplot_command_template' ].format( DS_FNAME= x[ 'dataset_fname'] )  for x in datasets_for_fit ] ) + "\n"
            

            datasets_for_plot = filter( lambda x : x['plottype'] in ['xyzt_gen', 'xy', 'expl_f']
                                                  , datasets )

            plt_call = "p {ST}".format(ST = ",\\\n".join(
                map( 
                    lambda x : x[ 'gnuplot_command_template' ].format( DS_FNAME = x[ 'dataset_fname' ] , OPTS =  x[ 'gnuplot_opt' ]  )
                    , datasets_for_plot
                )
            )
            )
            
            calls.append(alterations_t + fit_call + plt_call)
            mp_count += 1

        return "\n".join(calls)

    def __generate_gnuplot_file_content(self):
        redended_variables = self.__render_variables()
        parameters_string = "\n".join(self.global_plotting_parameters) + "\n"        


        plotting_string = self.__generate_gnuplot_plotting_calls()

        final_content = "\n".join([ redended_variables ,  parameters_string , plotting_string ])

        return final_content

    def print_gnuplot_file_content(self, highlight = True, linenos = 'inline'):
        """Displays the content of the gnuplot file generated. Intended for debug.

        Parameters
        ----------------
        highlight: bool, optional
             (True) Uses `pygments` to color the gnuplot script. 
        linenos: string, optional
             ("inline") Parameter `linenos` forwarded to the `pygments` `HtmlFormatter` object.  
        """
        
        final_content = self.__generate_gnuplot_file_content()
        try:
            from IPython.display import display, HTML
            get_ipython
        except:
            # jupyter seems not there..
            highlight = False
        
        if highlight and pygments_support_enabled:
            warnings.warn("This function benefits from pygments when installed.")
            
            from pygments import highlight
            from pygments.lexers import GnuplotLexer
            from pygments.formatters import HtmlFormatter

            from pygments.styles import get_style_by_name
             

            from IPython.core.display import display, HTML
            html__ =  highlight(final_content,
                                GnuplotLexer(),
                                HtmlFormatter(style='colorful',
                                              noclasses = False,
                                              linenos=linenos))
            display(HTML("""
            <style>
            {pygments_css}
            </style>
            """.format(pygments_css=HtmlFormatter().get_style_defs('.highlight'))))
            
            display(HTML( html__ ) )
            #print(html__)
        else:            
            print (final_content)

    def get_gnuplot_file_content(self):
        """returns the gnuplot core file content as a string
        """
        return self.__generate_gnuplot_file_content()
    

    def generate_gnuplot_file(self):
        """Generates the final gnuplot scripts without creating any figure. Includes: `Makefile`, `.gitignore` and synchronization scripts.
        """

        final_content = self.__generate_gnuplot_file_content()

        ### CORE FILE
        self.__core_gnuplot_file = self.global_file_identifier + "__.core.gnu"
        self.__local_core_gnuplot_file = self.file_identifier + "__.core.gnu"
        
        with open( self.__core_gnuplot_file  , 'w'  ) as f:            
            f.write(final_content)

        
        ### JPG terminal
        self.__local_jpg_gnuplot_file = self.file_identifier + "__.jpg.gnu"
        self.__jpg_gnuplot_file = self.globalize_fname(self.__local_jpg_gnuplot_file)


        self.__local_jpg_output  = self.file_identifier + "__.jpg"
        self.__jpg_output = self.globalize_fname(self.__local_jpg_output)
        
        with open( self.__jpg_gnuplot_file , 'w' ) as f:
            f.write(
                autognuplot_terms.JPG_wrapper_file.format(
                    OUTFILE = self.__local_jpg_output
                     , CORE =   self.__local_core_gnuplot_file   )
                )

        #### gitignore
        self.__gitignore_file = self.globalize_fname(".gitignore")
        with open( self.__gitignore_file, 'w' ) as f:
            f.write(
                autognuplot_terms.GITIGNORE_wrapper_file                
            )
        
        
        #### pdflatex terminal
        self.__local_pdflatex_output = self.file_identifier + "__.pdf"
        self.__pdflatex_output = self.globalize_fname( self.__local_jpg_output )

        ##used to be a jpg, yet png is much better
        self.__local_pdflatex_output_jpg_convert = self.__local_pdflatex_output + "_converted_to.png" 
        self.__pdflatex_output_jpg_convert = self.globalize_fname( self.__local_pdflatex_output_jpg_convert )
        

        self.__local_pdflatex_gnuplot_file = self.file_identifier + "__.pdflatex.gnu"
        self.__pdflatex_gnuplot_file = self.globalize_fname(self.__local_pdflatex_gnuplot_file)

        self.__local_pdflatex_compilesh_gnuplot_file = self.file_identifier + "__.pdflatex_compile.sh"
        self.__pdflatex_compilesh_gnuplot_file = self.globalize_fname(self.__local_pdflatex_compilesh_gnuplot_file)
        
        with open( self.__pdflatex_gnuplot_file, 'w'  ) as f:
            f.write(
                autognuplot_terms.LATEX_wrapper_file.format(
                    CORE = self.__local_core_gnuplot_file
                    , **self.pdflatex_terminal_parameters
                    )
            )

        with open ( self.__pdflatex_compilesh_gnuplot_file , 'w' ) as f:
            f.write(
                autognuplot_terms.LATEX_compile_sh_template.format(
                    LATEX_TARGET_GNU = self.__local_pdflatex_gnuplot_file
                    , FINAL_PDF_NAME = self.__local_pdflatex_output
                    , FINAL_PDF_NAME_jpg_convert = self.__local_pdflatex_output_jpg_convert
                    , pdflatex_jpg_convert_density = self.pdflatex_jpg_convert_density
                    , pdflatex_jpg_convert_quality = self.pdflatex_jpg_convert_quality
                )
            )
        ## the tikz part is refactored into a dedicated function
        self.__generate_gnuplot_files_tikz()
        

    def __generate_gnuplot_files_tikz(self):
        self.__local_tikz_output = self.file_identifier + "__.tikz.pdf"
        self.__tikz_output = self.globalize_fname( self.__local_tikz_output )

        self.__local_tikz_output_jpg_convert = self.__local_tikz_output + "_converted_to.jpg"
        self.__tikz_output_jpg_convert = self.globalize_fname( self.__local_tikz_output_jpg_convert )
        

        self.__local_tikz_gnuplot_file = self.file_identifier + "__.tikz.gnu"
        self.__tikz_gnuplot_file = self.globalize_fname(self.__local_tikz_gnuplot_file)

        self.__local_tikz_compilesh_gnuplot_file = self.file_identifier + "__.tikz_compile.sh"
        self.__tikz_compilesh_gnuplot_file = self.globalize_fname(self.__local_tikz_compilesh_gnuplot_file)
        
        with open( self.__tikz_gnuplot_file, 'w'  ) as f:
            f.write(
                autognuplot_terms.TIKZ_wrapper_file.format(
                    CORE = self.__local_core_gnuplot_file
                    , **self.pdflatex_terminal_parameters ## maybetochange?
                    )
            )

        with open ( self.__tikz_compilesh_gnuplot_file , 'w' ) as f:
            f.write(
                autognuplot_terms.TIKZ_compile_sh_template.format(
                    TIKZ_TARGET_GNU = self.__local_tikz_gnuplot_file
                    , FINAL_PDF_NAME = self.__local_tikz_output
                    , FINAL_PDF_NAME_jpg_convert = self.__local_tikz_output_jpg_convert
                    , pdflatex_jpg_convert_density = self.pdflatex_jpg_convert_density
                    , pdflatex_jpg_convert_quality = self.pdflatex_jpg_convert_quality
                )
            )

    def __jupyter_show_generic(self
                               , command_to_call
                               , image_to_display
                               , show_stderr = True
                               , show_stdout = False
                               , height = None
                               , width = None):
        
        from subprocess import Popen as _Popen, PIPE as _PIPE, call as _call

        if self.verbose:
            print ("trying call: ", command_to_call)
            
        proc = _Popen(command_to_call
                      , shell=False
                      , universal_newlines=True
                      , cwd = self.folder_name
                      , stdout=_PIPE
                      , stderr=_PIPE)
        output, err = proc.communicate()

        #amending for the fit output
        was_there_an_error = \
            "error" in output or\
            "Error" in output or\
            "error" in err or\
            ("Error" in err and not "Standard Error" in err) or\
            proc.returncode != 0
        
        if was_there_an_error:
            
            # diagnosing pdflatex installation problem
            if "pdflatex: command not found" in err:
                print("ERROR: PDFLATEX is NOT installed.\n")
            elif "gnuplot: command not found" in err:
                print("ERROR: GNUPLOT is NOT installed.\n")
            else:
                print("ERROR: an error was intercepted.")
            
            
            print("  stderr and stdout reported below for diagnostics.")
            print("")
        
        
        if self.verbose:
            print ("After running _Popen, was_there_an_error is", was_there_an_error)
    
        if show_stderr or self.verbose or was_there_an_error:
            print ("===== stderr =====")
            print (err)
            print ("=== stderr end ===")
        if show_stdout or self.verbose or was_there_an_error:
            print ("===== stdout =====")
            print (output)
            print ("=== stdout end ===")

        if not was_there_an_error:
            from IPython.core.display import Image, display
            display(Image( image_to_display, height=height, width=width  ))

    

    def jupyter_show(self                     
                     , show_stdout = False):
        """Generates a figure via the jpg terminal and opens it in jupyter.
        The more advanced `jupyter_show_pdflatex` and `jupyter_show_tikz` are advised. This call is left for debug.

        Parameters
        ----------------
        show_stdout: bool, optional
             (False) outputs `stdout` and `stderr` to screen.
        """
        from subprocess import Popen as _Popen, PIPE as _PIPE, call as _call

        if self.verbose:
            print ("trying call: ", ["gnuplot", self.__jpg_gnuplot_file ])

        proc = _Popen(["gnuplot", self.__local_jpg_gnuplot_file ] , shell=False,  universal_newlines=True, cwd = self.folder_name, stdout=_PIPE, stderr=_PIPE)
        output, err = proc.communicate()

        if show_stdout:
            print ("===== stderr =====")
            print (err)
            print ("===== stdout =====")
            print (output)


        from IPython.core.display import Image, display
        display(Image( self.__jpg_output  ))

    def jupyter_show_pdflatex(self
                              , show_stdout = False
                              , show_stderr = False
                              , width = None
                              , height = None ):

        """Shows a pdflatex rendering within the current jupyter notebook.

        
        To work it requires ImageMagick and authorization to render pdf to jpg. 
        Should it fail:
        https://stackoverflow.com/a/52661288
        """
        self.__jupyter_show_generic(
            [ "bash", self.__local_pdflatex_compilesh_gnuplot_file  ]
            , self.__pdflatex_output_jpg_convert
            , height = height
            , width = width
            , show_stderr = show_stderr 
            , show_stdout = show_stdout 
        )

    def jupyter_show_tikz(self
                          , show_stderr = False
                          , show_stdout = False                          
                          , height = None
                          , width = None):

        r"""Shows a pdflatex rendering within the current jupyter notebook.

        To work it requires ImageMagick and authorization to render pdf to jpg. 
        Should it fail:
        https://stackoverflow.com/a/52661288

        LUA compilation issue: https://tex.stackexchange.com/a/368194
        solution: 
        in `/usr/share/gnuplot5/gnuplot/5.0/lua/gnuplot-tikz.lua`, replace:

        
        pgf.set_dashtype = function(dashtype)
        gp.write("\\gpsetdashtype{"..dashtype.."}\n")
        end
        
        with
        
        pgf.set_dashtype = function(dashtype)
        gp.write("%\\gpsetdashtype{"..dashtype.."}\n")
        end

        """      

        self.__jupyter_show_generic(
            [ "bash", self.__local_tikz_compilesh_gnuplot_file  ]
            , self.__tikz_output_jpg_convert
            , height = height
            , width = width
            , show_stderr = show_stderr 
            , show_stdout = show_stdout 
        )

        

    def __establish_ssh_info(self
                             , hostname= None):
        """Generates the string containing the signifcant scp call for copying.

        :param hostname: str
        (None) Overrides the default hostname. Use in case the default hostname is unsuitable for scp copies.
        """
        import socket
        import getpass
        hostname = hostname if hostname is not None else socket.gethostname()
        self.__ssh_string = "{user}@{hostname}:{dir_}".format(user=getpass.getuser()
                                                      , hostname=hostname
                                                      , dir_=self.global_dir_whole_path )

        self.__scp_string = "scp -r " + self.__ssh_string + " ."
        self.__scp_string_nofolder = "scp -r " + self.__ssh_string +"/*" + " ."

    def display_fixes(self):
        """displays relevant fixes in case the `convert` call does not work or to solve a known gnuplot/luatex bug. 
        """
        fixes_ =\
"""
These are some fixes found for imagemagick and gnuplot tikz terminal


Shows a pdflatex rendering within the current jupyter notebook.
To work it requires ImageMagick and authorization to render pdf to jpg. 
Should it fail:
https://stackoverflow.com/a/52661288

Concisely: sudo sed -i '/PDF/s/none/read|write/' /etc/ImageMagick-6/policy.xml

LUA compilation issue: https://tex.stackexchange.com/a/368194
solution: 
in /usr/share/gnuplot5/gnuplot/5.0/lua/gnuplot-tikz.lua, Replace:
pgf.set_dashtype = function(dashtype)
gp.write("\\gpsetdashtype{"..dashtype.."}\n")
end


with:
pgf.set_dashtype = function(dashtype)
gp.write("%\\gpsetdashtype{"..dashtype.."}\n")
end
"""

        print (fixes_)
        return fixes_

        
    def get_folder_info(self):
        from IPython.display import display, HTML

        if self.is_anonymous:
            raise Exception("get_folder_info disabled for anonymous figures.")

        infos = [
            ["(folder local):", self.folder_name ]
            , ["(folder global):", self.global_dir_whole_path]
            , ["(ssh):",  self.__ssh_string]
            , ["(autosync):", "echo '{scp_string}' > retrieve_{fold_name}.sh ; bash retrieve_{fold_name}.sh ".format(
                scp_string = self.__scp_string
                , fold_name = self.folder_name.replace("/","__")
            ) 
            ]            
        ]
        
        try:
            get_ipython
            display(HTML(
                '<table><tr>{}</tr></table>'.format(
                    '</tr><tr>'.join(
                        '<td>{}</td>'.format('</td><td>'.join(str(_) for _ in row)) for row in infos)
                )
            ))

        except:        
            print ("(folder local): ", self.folder_name)
            print ("(folder global): ", self.global_dir_whole_path)
            print ("(ssh): " + self.__ssh_string  )

            print ("(scp): " + self.__scp_string )
            print ("(autosync): ")
            print ("      echo '{scp_string}' > retrieve_{fold_name}.sh ; bash retrieve_{fold_name}.sh ".format(
                  scp_string = self.__scp_string
                , fold_name = self.folder_name.replace("/","__")
            )   )

    def print_folder_info(self):
        """Proxy for get_folder_info
        """
        self.get_folder_info()

    def print_latex_fig_inclusion_code(self):
        return self.print_latex_snippet()

    def print_latex_snippet(self):
        """Propts latex code that can be used to include the figure.
        
        For the moment requires a call to self.generate_gnuplot_file()
        """

        if self.is_anonymous:
            raise Exception("print_latex_snippet disabled for anonymous figures.")
        
        self.generate_gnuplot_file()

        latex_incl_statement = plot_helpers.latex_document_include_figure_statement(
            self.folder_name + '/' + self.__local_pdflatex_output.replace(".pdf","") #strips out extension
            , self.folder_name + '/' + self.__local_tikz_output.replace(".pdf","")
            , tikz_enabled = self.terminals_enabled_by_default['tikz']['is_enabled']
        )


        try:
            from IPython.display import display, HTML
            get_ipython
            highlight = True
        except:
            # jupyter seems not there..
            highlight = False
        
        if pygments_support_enabled and highlight:            
            from pygments import highlight
            from pygments.lexers import TexLexer
            from pygments.formatters import HtmlFormatter

            from pygments.styles import get_style_by_name

            html__ =  highlight(latex_incl_statement,
                                TexLexer(),
                                HtmlFormatter(style='colorful',
                                              noclasses = False,
                                              linenos=False))
            display(HTML("""
            <style>
            {pygments_css}
            </style>
            """.format(pygments_css=HtmlFormatter().get_style_defs('.highlight'))))
            
            display(HTML( html__ ) )
            
        else:
            print(latex_incl_statement)

    
            
                          
        
        
        
