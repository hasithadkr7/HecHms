"""
@file
@brief Installs and loads an extension.
"""
import os
from notebook.nbextensions import install_nbextension
from IPython.display import HTML


def install_extension(ext, overwrite=False):
    """
    Installs an extension.

    @param  ext         extension name
    @param  overwrite   overwrite
    @return             installation path
    """
    this = os.path.dirname(__file__)
    path = os.path.join(this, ext)
    if not os.path.exists(path):
        raise FileNotFoundError(
            "Unable to find extension '{0}' in '{1}'".format(ext, this))
    dest = install_nbextension(
        path, user=True, destination=ext, overwrite=overwrite)
    return dest


def load_extension(ext, kind='html', overwrite=False):
    """
    Loads an extension.

    @param  ext         extension name
    @param  overwrite   overwrite
    @param  kind        ``'html'`` or ``'str'``
    @return             HTML object
    """
    dest = install_extension(ext, overwrite=overwrite)
    files = os.listdir(dest)
    css = [_ for _ in files if _.endswith('.css')]
    js = [_ for _ in files if _.endswith('.js')]
    code = """<script>
                var load_jyq_css___EXT__ = function(cssfile) {
                    var link = document.createElement("link");
                    link.type = "text/css";
                    link.rel = "stylesheet";
                    link.href = require.toUrl(cssfile);
                    document.getElementsByTagName("head")[0].appendChild(link);
                };
                __CSS__
                require([__REQ__]);\n
                </script>
                <p>Loads extension '__EXT__'.</p>""".replace("                ", "")
    code = code.replace('__EXT__', ext)
    code = code.replace('__REQ__', ',\n'.join(
        "'{0}/{1}'".format(ext, _) for _ in js))
    code = code.replace('__CSS__', ';\n'.join(
        "load_jyq_css_{0}('{0}/{1}')".format(ext, _) for _ in css) + ';')
    if kind == "html":
        return HTML(code)
    else:
        return code
