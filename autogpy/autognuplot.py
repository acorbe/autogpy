### makes it easy to pass data to gnuplot - plotting tools - dumps data and generates one elementary plotting script
from __future__ import print_function

import os
import numpy as np
from collections import OrderedDict

from . import autognuplot_terms

class AutoGnuplotFigure(object):
    """Creates an AutoGnuplotFigure object wrapping one gnuplot figure.

        :param folder_name: target location for the figure scripts and data
        :type folder_name: str
        :param file_identifier: common identifier present in the file names of this figure object
        :type file_identifier: str
        :param verbose:  (False) Verbose operating mode.
        :type verbose: bool
        :param autoescape:  (True) Autoescapes latex strings. It enables to use latex directly in raw strings without further escaping.
        :type verbose: bool


        Usage:

        >>> fig = AutoGnuplotFigure('folder','id')
        >>> fig.p_generic('u 1 : 2 t "my title" ', x ,y)
        >>> fig.generate_gnuplot_file()
        >>> fig.jupyter_show_pdflatex(show_stdout=False)

        Class members to be changed:

        >>> fig.pdflatex_terminal_parameters = 
        >>> {
        >>>     "x_size" : "9.9cm"
        >>>     , "y_size" : "8.cm"
        >>>     , "font" : "phv,12 "
        >>>     , "linewidth" : "2"
        >>> }

    """

    def __init__(self
                 , folder_name
                 , file_identifier
                 , verbose = False
                 , autoescape = True):
        """ AutoGnuplotFigure

        """
        

        self.verbose = verbose
        
        self.folder_name = folder_name
        self.global_dir_whole_path = os.getcwd() + '/' +  self.folder_name
        self.file_identifier = file_identifier

        if not os.path.exists(self.folder_name):
            os.makedirs(self.folder_name)
            if verbose:
                print( "created folder:", self.folder_name )

        self.global_file_identifier = self.folder_name + '/' + self.file_identifier
        self.globalize_fname = lambda x : self.folder_name + '/' + x

        self.__establish_ssh_info()
        

        self.dataset_counter = 0

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

        }
        self._autoescape = autoescape

        self.variables = OrderedDict()

        with open( self.globalize_fname("Makefile"), "w" ) as f:
            f.write(  autognuplot_terms.MAKEFILE_LATEX  )

        with open( self.globalize_fname("sync_me.sh"), "w" ) as f:
            f.write(  autognuplot_terms.SYNC_sc_template.format(
                SYNC_SCP_CALL = self.__scp_string_nofolder
            )
            )
        
        

    def extend_global_plotting_parameters(self, *args, **kw):
        """Extends the preamble of the gnuplot script to modify the plotting settings. 
        Expects one or more strings with gnuplot syntax.
 
        >>> figure.extend_global_plotting_parameters(
        >>> r\"\"\"
        >>> set mxtics 2
        >>> set mytics 1
        >>> 
        >>> # color definitions
        >>> set border linewidth 1.5
        >>> set style line 1 lc rgb '#ff0000'  lt 1 lw 2
        >>> set style line 2 lc rgb '#0000ff' lt 3 lw 4
        >>> 
        >>> # Axes
        >>> set style line 11  lc rgb '#100100100' lt 1
        >>> set border 3 back ls 11
        >>> set tics nomirror out scale 0.75
        >>> # Grid
        >>> set style line 12 lc rgb'#808080' lt 0 lw 1
        >>> set grid back ls 12
        >>> 
        >>> set format y '$%.4f$'
        >>> set format x '$%.4f$'
        >>> 
        >>> set key top left
        >>> 
        >>> set key samplen 2 inside spacing 1 width 0.3 height 1.5  at graph 0.99, 1.05
        >>> 
        >>> unset grid
        >>> #set logscale y
        >>> set xlabel "$\\nu$"
        >>> set xrange [1e-5:1.05e-3]
        >>> set yrange [1e-5:1e-3]
        >>> set xtics 0,2e-4,1.01e-3
        >>> #set ytics 2e-4,2e-4,1.01e-3
        >>> \"\"\")        

        """
        autoescape = kw.get("autoescape", self._autoescape)
        escaped_args = []
        if autoescape:
            for idx,a in enumerate(args):
                escaped_args.append(self.__autoescape_strings(a))
            self.global_plotting_parameters.extend(escaped_args)
        else:
            self.global_plotting_parameters.extend(args)

    def set_multiplot(self, specifiers = ""):
        """Enables multiplot mode (use in combination with :next_multiplot_group). Multiplot arguments are passed via the kw `specifiers`"""
        
        self.is_multiplot = True
        self.extend_global_plotting_parameters(
            "set multiplot " + specifiers
        )

    def next_multiplot_group(self):
        if not self.is_multiplot:
            raise Exception("set_multiplot() is expected to use this feature")
        self.multiplot_index += 1
        self.datasets_to_plot.append([])
        self.alter_multiplot_state.append([])

    def alter_current_multiplot_parameters(self,*args,**kw):
        autoescape = kw.get("autoescape", self._autoescape)
        escaped_args = []
        if autoescape:
            for idx,a in enumerate(args):
                escaped_args.append(self.__autoescape_strings(a))
            self.alter_multiplot_state[self.multiplot_index].extend(escaped_args)            
        else:
            self.alter_multiplot_state[self.multiplot_index].extend(args)        
        

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

        x = np.array(x)
        y = np.array(y)
        data = np.concatenate([x[:,np.newaxis] ,y[:,np.newaxis]  ],axis = 1)
        dataset_fname = self.file_identifier + self.datasetstring_template.format(            
            DS_ID = self.dataset_counter
            , SPECS = fname_specs)
        
        np.savetxt( self.globalize_fname(dataset_fname) ,  data)

        
        self.__append_to_multiplot_current_dataset(
            {'dataset_fname' : dataset_fname
             , 'plottype' : 'xy'
             , 'gnuplot_opt' : gnuplot_opt
             , 'gnuplot_command_template' : """ "{DS_FNAME}" u 1:2 {OPTS}  """

            }

        )
        self.dataset_counter += 1

    def __hist_normalization_function(self
                                      , v_
                                      , normalization ):

        N_coeff = 1.
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
                     , reweight = lambda edges_mid : 1.
                     , **kw
                    ):

        v_, e_ = np.histogram(x,**hist_kw)
        edges_mid = .5 * (e_[1:] + e_[:-1])
        
        
        if kde:
            from scipy.stats import gaussian_kde
            kernel = gaussian_kde(x,**kde_kw)

            kde_vals = kernel(edges_mid)

            v_ = kde_vals        
            
        v_ *= reweight(edges_mid)                   

        N_coeff = self.__hist_normalization_function(v_,normalization)
        v_ /= N_coeff
        
        self.p_generic(
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
        """proxies the interface of plt.hist for a rapid call swap. 
        Adds "gnuplot_command_no_u" and "title" arguments """

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
        """Central plotting primitive"""
        fname_specs = kw.get("fname_specs","")
        autoescape = kw.get("autoescape",self._autoescape)

        if autoescape:
            command_line = self.__autoescape_strings(command_line)

            if self.verbose:
                print("autoescaping -- processing:", command_line)
        
        #prepend_parameters = kw.get("prepend_parameters",[""])
        #fname_specs = ""

        if len(args) == 0: #case an explicit function is plotted:

            print ("To be tested")
            
            self.__append_to_multiplot_current_dataset(
                {'dataset_fname' : ""
                 , 'plottype' : 'expl_f'
                 , 'gnuplot_opt' : ""
                 , 'gnuplot_command_template' : command_line
                 #, 'prepended_parameters' : prepend_parameters
                }
            )            
        else:            
        
            xyzt = list(map( lambda x : np.array(x)[: , np.newaxis ], args  ))

            data = np.concatenate( xyzt , axis = 1 )

            dataset_fname = self.file_identifier + self.datasetstring_template.format(            
                DS_ID = self.dataset_counter
                , SPECS = fname_specs)

            np.savetxt( self.globalize_fname(dataset_fname) ,  data)

            if '"{DS_FNAME}"' not in command_line:
                if self.verbose:
                    print('Warning: "{DS_FNAME}" will be prepended to your string')
                command_line = '"{DS_FNAME}"' + " " + command_line

            self.__append_to_multiplot_current_dataset(
                {'dataset_fname' : dataset_fname
                 , 'plottype' : 'xyzt_gen'
                 , 'gnuplot_opt' : ""
                 , 'gnuplot_command_template' : command_line
                 #, 'prepended_parameters' : prepend_parameters
                }
            )
            self.dataset_counter += 1

    def add_variable_declaration(self,name,value,is_string = False):
        self.variables[name] = "'%s'"%str(value) if is_string else str(value)
        
        #self.global_plotting_parameters.append(  "{NAME}={VALUE}".format(NAME = name, VALUE = "'%s'"%str(value) if is_string else str(value) ) )
    def render_variables(self):

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

    def generate_gnuplot_file_content(self):
        redended_variables = self.render_variables()
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
        final_content = self.generate_gnuplot_file_content()
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

        final_content = self.generate_gnuplot_file_content()

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
            print (output)
            print (err)

        from IPython.core.display import Image, display
        display(Image( self.__jpg_output  ))

    def jupyter_show_pdflatex(self
                              , show_stdout = False ):

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
            print (output)
            print (err)

        from IPython.core.display import Image, display
        print("opening:", self.pdflatex_output_jpg_convert)
        display(Image( self.pdflatex_output_jpg_convert  ))


    def jupyter_show_tikz(self
                          , show_stdout = False ):

        """Shows a pdflatex rendering within the current jupyter notebook.
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
        

    
            
                          
        
        
        
