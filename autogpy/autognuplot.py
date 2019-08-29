### makes it easy to pass data to gnuplot - plotting tools - dumps data and generates one elementary plotting script
from __future__ import print_function

import os
import numpy as np
from collections import OrderedDict

from . import autognuplot_terms


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

        Returns
        --------------------
        fig : AutoGnuplotFigure


        Examples
        ----------------

        >>> fig = AutoGnuplotFigure('folder','id')
        >>> # for some existing arrays x,y
        >>> fig.p_generic('u 1 : 2 t "my title" ', x ,y) 
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
                 , file_identifier
                 , verbose = False
                 , autoescape = True
                 , latex_enabled = True
                 , tikz_enabled = False
                 , allow_strings = False):
        """ AutoGnuplotFigure

        """
        

        self.verbose = verbose
        
        self.folder_name = folder_name
        self.global_dir_whole_path = os.getcwd() + '/' +  self.folder_name
        self.file_identifier = file_identifier

        if not os.path.exists(self.folder_name):
            os.makedirs(self.folder_name)
            if self.verbose:
                print( "created folder:", self.folder_name )

        self.global_file_identifier = self.folder_name + '/' + self.file_identifier
        self.globalize_fname = lambda x : self.folder_name + '/' + x

        # will get name of user/host... This allows to create the scp copy script 
        self.__establish_ssh_info()
        
        self.__dataset_counter = 0 

        self.datasetstring_template = "__{DS_ID}__{SPECS}.dat"

        self.datasets_to_plot = [ [] ]
        self.alter_multiplot_state = [  []  ] #the first altering block can be just global variables
        
        self.multiplot_index = 0
        self.is_multiplot = False
        
        self.global_plotting_parameters = []


        self.pdflatex_jpg_convert_density = 300
        self.pdflatex_jpg_convert_quality = 90
        
        self.pdflatex_terminal_parameters = {
            "x_size" : "9.9cm"
            , "y_size" : "8.cm"
            , "font" : "phv,12 "
            , "linewidth" : "2"
            , "other" : ""

        }
        self._autoescape = autoescape

        self.variables = OrderedDict()

        self.terminals_enabled_by_default =[
            {'type' : 'latex', 'is_enabled' : latex_enabled
             , 'makefile_string' : '$(latex_targets_pdf)'}
            , {'type' : 'tikz', 'is_enabled' : tikz_enabled
             , 'makefile_string' : '$(tikz_targets_pdf)'}
        ]


        self.__Makefile_replacement_dict = { 
            'TAB' : "\t"  #ensure correct tab formatting
            , 'ALL_TARGETS' : "" + " ".join(
                [ x['makefile_string'] for x in self.terminals_enabled_by_default if x['is_enabled'] ]
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
        escaped_args = []
        if autoescape:
            for idx,a in enumerate(args):
                escaped_args.append(self.__autoescape_strings(a))
            self.global_plotting_parameters.extend(escaped_args)
        else:
            self.global_plotting_parameters.extend(args)

        return self

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
        """Deprecated: Makes a x-y plot. Use `p_generic` instead.
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
             (False) a gaussian kernel will be used to histogram the data, edges used are from the np.histogram call
        kde_kw: dict, optional
             ({}) parameters to pass to the `scipy.stats.gaussian_kde` call
        reweight: function, optional
             (`lambda: edges_mid : 1`) function to reweight the histogram or kde values. Receives the bin center as parameter.
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
        
        return self.p_generic(
            gnuplot_command_using + " " + gnuplot_command_no_u
            , edges_mid , v_
            , **kw
        )

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
        
        
    def __autoescape_strings(self, command_line):
        command_line = command_line.replace("\\","\\\\")
        command_line = command_line.replace("{","{{")
        command_line = command_line.replace("}","}}")

        #preserves some needed blocks
        command_line = command_line.replace("{{DS_FNAME}}","{DS_FNAME}" )
        return command_line

    def p_generic(self, command_line, *args, **kw):
        """Central plotting primitive.
                
        Arguments
        ----------
        command_line: string
             gnuplot command, without the explicit call to plot and the filename of the content
        *args: lists or np.array, optional
             columns with the data, one or more columns can contain strings (e.g. for labels). In this case 'allow_strings' must be True.
        fname_specs: string, optional
             ("") allows to specify a filename for the data different for the default one.
        autoescape: bool, optional
             (as set in by the constructor) allows to selectively modify the class setting for autoescaping
        allow_strings: bool, optional
             (False) set to True to allows columns with strings. This requires pandas. Might become True by default in the future.             

        """
        fname_specs = kw.get("fname_specs","")
        autoescape = kw.get("autoescape",self._autoescape)
        allow_strings = kw.get("allow_strings",self._allow_strings)
        column_names = kw.get("column_names",None)

        if autoescape:
            command_line = self.__autoescape_strings(command_line)

            if self.verbose:
                print("autoescaping -- processing:", command_line)
        
        #prepend_parameters = kw.get("prepend_parameters",[""])
        #fname_specs = ""

        if len(args) == 0: #case an explicit function is plotted:

            print ("To be tested")

            to_append = \
                {'dataset_fname' : ""
                 , 'plottype' : 'expl_f'
                 , 'gnuplot_opt' : ""
                 , 'gnuplot_command_template' : command_line
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

            if allow_strings:
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
                print(xyzt) 

                ##########

            else:
                # numpy way
                try:
                    xyzt = list(map( lambda x : np.array(x)[: , np.newaxis ], args  ))
                    data = np.concatenate( xyzt , axis = 1 )
                    np.savetxt( globalized_dataset_fname ,  data)
                except TypeError:
                    print("\nWARNING: You got this exception likely beacuse you have columns with strings.\n"
                          "Please set 'allow_strings' to True.")
                    raise
                

            if '"{DS_FNAME}"' not in command_line:
                if self.verbose:
                    print('Warning: "{DS_FNAME}" will be prepended to your string')
                command_line = '"{DS_FNAME}"' + " " + command_line
            if " t " not in command_line \
               and " t\"" not in command_line\
               and " title " not in command_line\
               and " title\"" not in command_line:

                command_line =  command_line + " " + """title "{TITLE}" """.format(TITLE = dataset_fname.split('/')[-1].replace("_","\\\_"))
                if self.verbose:
                    print('Warning: a title will be appended to avoid latex compilation problems')
                    print('the final command reads:')
                    print(command_line)

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
        

    def add_variable_declaration(self,name,value,is_string = False):
        self.variables[name] = "'%s'"%str(value) if is_string else str(value)
        
        #self.global_plotting_parameters.append(  "{NAME}={VALUE}".format(NAME = name, VALUE = "'%s'"%str(value) if is_string else str(value) ) )
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
            plt_call = "p {ST}".format(ST = ",\\\n".join(
                map( 
                    lambda x : x[ 'gnuplot_command_template' ].format( DS_FNAME = x[ 'dataset_fname' ] , OPTS =  x[ 'gnuplot_opt' ]  )
                    , datasets
                )
            )
            )

            calls.append(alterations_t + plt_call)
            mp_count += 1

        return "\n\n".join(calls)

    def __generate_gnuplot_file_content(self):
        redended_variables = self.__render_variables()
        parameters_string = "\n".join(self.global_plotting_parameters) + "\n\n"
        

        

        # plotting_string =  "p {ST}".format(ST = ",\\\n".join(
        #     map(
        #         lambda x : x[ 'gnuplot_command_template' ].format( DS_FNAME = x[ 'dataset_fname' ] , OPTS =  x[ 'gnuplot_opt' ]  )
        #         , self.datasets_to_plot
        #     )
        # )
        # )

        plotting_string = self.__generate_gnuplot_plotting_calls()

        final_content = "\n".join([ redended_variables ,  parameters_string , plotting_string ])

        return final_content

    def print_gnuplot_file_content(self, highlight = True):
        """Displays the content of the gnuplot file generated. Intended for debug.

        Parameters
        ----------------
        highlight: bool, optional
             (False) Uses `pygaments` to color the gnuplot script
        """
        final_content = self.__generate_gnuplot_file_content()
        if highlight:
            from pygments import highlight
            from pygments.lexers import GnuplotLexer
            from pygments.formatters import HtmlFormatter

            from pygments.styles import get_style_by_name
             

            from IPython.core.display import display, HTML
            html__ =  highlight(final_content, GnuplotLexer(), HtmlFormatter(style='colorful', noclasses = False))
            display(HTML("""
            <style>
            {pygments_css}
            </style>
            """.format(pygments_css=HtmlFormatter().get_style_defs('.highlight'))))
            
            display(HTML( html__ ) )
            #print(html__)
        else:
        
            
            print (final_content)

        
    

    def generate_gnuplot_file(self):
        """Generates the final gnuplot scripts without creating any figure. Inclides Makefiles
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

        #### pdflatex terminal
        self.local_pdflatex_output = self.file_identifier + "__.pdf"
        self.pdflatex_output = self.globalize_fname( self.__local_jpg_output )

        self.local_pdflatex_output_jpg_convert = self.local_pdflatex_output + "_converted_to.jpg"
        self.pdflatex_output_jpg_convert = self.globalize_fname( self.local_pdflatex_output_jpg_convert )
        

        self.local_pdflatex_gnuplot_file = self.file_identifier + "__.pdflatex.gnu"
        self.pdflatex_gnuplot_file = self.globalize_fname(self.local_pdflatex_gnuplot_file)

        self.local_pdflatex_compilesh_gnuplot_file = self.file_identifier + "__.pdflatex_compile.sh"
        self.pdflatex_compilesh_gnuplot_file = self.globalize_fname(self.local_pdflatex_compilesh_gnuplot_file)
        
        with open( self.pdflatex_gnuplot_file, 'w'  ) as f:
            f.write(
                autognuplot_terms.LATEX_wrapper_file.format(
                    CORE = self.__local_core_gnuplot_file
                    , **self.pdflatex_terminal_parameters
                    )
            )

        with open ( self.pdflatex_compilesh_gnuplot_file , 'w' ) as f:
            f.write(
                autognuplot_terms.LATEX_compile_sh_template.format(
                    LATEX_TARGET_GNU = self.local_pdflatex_gnuplot_file
                    , FINAL_PDF_NAME = self.local_pdflatex_output
                    , FINAL_PDF_NAME_jpg_convert = self.local_pdflatex_output_jpg_convert
                    , pdflatex_jpg_convert_density = self.pdflatex_jpg_convert_density
                    , pdflatex_jpg_convert_quality = self.pdflatex_jpg_convert_quality
                )
            )
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


    def jupyter_show(self
                     , show_stdout = False):
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
                              , width = None
                              , height = None ):

        """Shows a pdflatex rendering within the current jupyter notebook.

        
        To work it requires ImageMagick and authorization to render pdf to jpg. 
        Should it fail:
        https://stackoverflow.com/a/52661288
        """

        from subprocess import Popen as _Popen, PIPE as _PIPE, call as _call

        if self.verbose:
            print ("trying call: ", [  self.local_pdflatex_compilesh_gnuplot_file   ])
            print ("from folder_name: ", self.folder_name)

        proc = _Popen(["bash", self.local_pdflatex_compilesh_gnuplot_file  ]
                      , shell=False
                      ,  universal_newlines=True
                      , cwd = self.folder_name
                      , stdout=_PIPE
                      , stderr=_PIPE)
        output, err = proc.communicate()

        if show_stdout:
            print ("===== stderr =====")
            print (err)
            print ("===== stout =====")
            print (output)


        from IPython.core.display import Image, display
        if self.verbose:
            print("opening:", self.pdflatex_output_jpg_convert)
            
        display(Image( self.pdflatex_output_jpg_convert
                       , width = width
                       , height = height))


    def jupyter_show_tikz(self
                          , show_stdout = False ):

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
        


        
        pgf.set_dashtype = function(dashtype)
        gp.write("%\\gpsetdashtype{"..dashtype.."}\n")
        end

        """

        from subprocess import Popen as _Popen, PIPE as _PIPE, call as _call

        if self.verbose:
            print ("trying call: ", [  self.__local_tikz_compilesh_gnuplot_file   ])
            print ("from folder_name: ", self.folder_name)

        proc = _Popen(["bash", self.__local_tikz_compilesh_gnuplot_file  ]
                      , shell=False
                      ,  universal_newlines=True
                      , cwd = self.folder_name
                      , stdout=_PIPE
                      , stderr=_PIPE)
        output, err = proc.communicate()

        if show_stdout:
            print (output)
            print (err)

        from IPython.core.display import Image, display
        if self.verbose:
            print("opening:", self.__tikz_output_jpg_convert)
            
        display(Image( self.__tikz_output_jpg_convert  ))

        

    def __establish_ssh_info(self):
        import socket
        import getpass
        self.__ssh_string = "{user}@{hostname}:{dir_}".format(user=getpass.getuser()
                                                      , hostname=socket.gethostname()
                                                      , dir_=self.global_dir_whole_path )

        self.__scp_string = "scp -r " + self.__ssh_string + " ."
        self.__scp_string_nofolder = "scp -r " + self.__ssh_string +"/*" + " ."

    def display_fixes(self):
        fixes_ =\
"""
These are some fixes found for imagemagick and gnuplot tikz terminal


Shows a pdflatex rendering within the current jupyter notebook.
To work it requires ImageMagick and authorization to render pdf to jpg. 
Should it fail:
https://stackoverflow.com/a/52661288

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
        
        print ("(folder local): ", self.folder_name)
        print ("(folder global): ", self.global_dir_whole_path)
        print ("(ssh): " + self.__ssh_string  )
        
        print ("(scp): " + self.__scp_string )
        print ("(autosync): ")
        print ("      echo '{scp_string}' > retrieve_{fold_name}.sh ; bash retrieve_{fold_name}.sh ".format(
              scp_string = self.__scp_string
            , fold_name = self.folder_name.replace("/","__")
        )   )
        

    
            
                          
        
        
        
