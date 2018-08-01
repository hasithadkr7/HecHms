# -*- coding: utf-8 -*-
"""
@file
@brief Renders a network in Javascript.
"""
import os
from .render_nb_js import RenderJS, JavascriptScriptError


class JavascriptVisError(JavascriptScriptError):
    """
    Raised when the code does not contain what the class expects to find.
    """
    pass


class RenderJsVis(RenderJS):
    """
    Renders a network in a :epkg:`notebook`
    with :epkg:`vis.js`.
    """

    def __init__(self, js=None, local=False, width="100%", height="100%", divid=None,
                 style=None, only_html=True, div_class=None, check_urls=True,
                 class_vis='Network', dot=None, layout=None, direction='UD'):
        """
        @param  js              (str) javascript
        @param  local           (bool) use local path to javascript dependencies
        @param  script          (str) script
        @param  width           (str) width
        @param  height          (str) height
        @param  style           (str) style (added in ``<style>...</style>``)
        @param  divid           (str|None) id of the div
        @param  only_html       (bool) use only function `display_html <http://ipython.readthedocs.io/en/stable/api/generated/IPython.display.html?highlight=display_html#IPython.display.display_html>`_
                                and not `display_javascript <http://ipython.readthedocs.io/en/stable/api/generated/IPython.display.html?highlight=display_html#IPython.display.display_javascript>`_ to add
                                javascript to the page.
        @param  div_class       (str) class of the section ``div`` which will host the results
                                of the javascript
        @param  check_urls      (bool) by default, check url exists
        @param  class_vis       (str) visualization class (*Network*, *Timeline*, ...)
        @param  dot             (str) either *js* or *dot* must be specified.
        @param  layout          (str) layout see `layout <http://visjs.org/docs/network/layout.html>`_
        @param  direction       (str) if ``layout=='hiearchical'``, a string among
                                `'UD'`, `'DU'`, `'LR'`, `'RL'`.

        The script must defined variables *options* and *data* if
        ``class_vis=='Network'``.
        """
        script = RenderJsVis._build_script(
            js, dot, layout=layout, direction=direction)
        libs, css = RenderJsVis._get_libs_css(local, class_vis)
        RenderJS.__init__(self, script, width=width, height=height, divid=divid,
                          only_html=only_html, div_class=div_class, check_urls=True,
                          libs=libs, css=css, local=local)

    @staticmethod
    def _get_libs_css(local, class_vis):
        """
        Returns the dependencies.

        @param      local       use local file (True) or remote urls (False)
        @param      lite        use lite version
        @return                 tuple *(libs, css)*
        """
        if class_vis == 'Network':
            libs = [  # 'vis-timeline-graph2d.min.js',
                #'vis-network.min.js',
                #'vis-graph3d.min.js',
                'vis.min.js'
            ]
            css = [  # 'vis-timeline-graph2d.min.css',
                'vis-network.min.css',
                'vis.min.css'
            ]
        else:
            raise NotImplementedError(
                "Unable to generate a script for class '{0}'".format(class_vis))

        if local:
            this = os.path.dirname(__file__)
            libs = [dict(path=os.path.join(this, '..', 'js',
                                           'visjs', j), name=j.split('.')[0]) for j in libs]
            css = [os.path.join(this, '..', 'js', 'visjs', j) for j in css]
        else:
            libs = [dict(path='http://www.xavierdupre.fr/js/visjs/' +
                         j, name=j.split('.')[0]) for j in libs]
            css = ['http://www.xavierdupre.fr/js/visjs/' + j for j in css]
        return libs, css

    @staticmethod
    def _build_script(js, dot, **options):
        """
        Builds the javascript script.

        @param      js      javascript
        @param      dot     dot scripts
        @param      options graph options
        @return             javascript
        """
        if js is None:
            if dot is None:
                raise ValueError("js or dot must be specified")
            else:
                dot = dot.replace("'", "\\'").replace("\n", "\\n")
                jsadd = """
                    var DOTstring = '%s';
                    var parsedData = vis.network.convertDot(DOTstring);
                    var data = { nodes: parsedData.nodes, edges: parsedData.edges };
                    var options = parsedData.options;
                """.replace("                    ", "") % dot
        else:
            if dot is not None:
                raise ValueError("js or dot must be specified not both")
            jsadd = js

        if options or 'var options =' not in jsadd:
            opts = {}
            if 'layout' in options and options['layout'] is not None:
                opts['layout'] = {options['layout']: {'direction': options.get('direction', 'UD'),
                                                      'sortMethod': "directed"}}
            else:
                opts = {k: v for k, v in options.items() if v is not None}
            st = 'var options = {0};'.format(RenderJsVis._options2js(opts))
            jsadd += "\n" + st + "\n"

        checks = ['var data =', 'var options =']
        for ch in checks:
            if ch not in jsadd:
                raise JavascriptVisError(
                    "String '{0}' was not found in\n{1}".format(ch, js))
        script = jsadd + "\nvar container = document.getElementById('__ID__');" + \
            "\nvar network = new vis.Network(container, data, options);\n"
        return script

    def _options2js(data):
        """
        Converts *data* into a string.
        """
        rows = ['{']
        for k, v in data.items():
            if k is None:
                raise ValueError("k cannot be None")
            rows.append(k)
            rows.append(':')
            if isinstance(v, dict):
                rows.append(RenderJsVis._options2js(v))
            else:
                rows.append('"{0}"'.format(v))
            rows.append(', ')
        rows.append('}')
        return "".join(rows)
