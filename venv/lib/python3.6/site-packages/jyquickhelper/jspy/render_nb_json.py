# -*- coding: utf-8 -*-
"""
@file
@brief Helpers around JSON
"""
import os
import shutil
import uuid
import json
from IPython.display import display_html, display_javascript


class RenderJSONRaw(object):
    """
    Renders :epkg:`JSON` in a :epkg:`notebook`
    using :epkg:`renderjson`.
    """

    def __init__(self, json_data, width="100%", height="100%", divid=None,
                 show_to_level=None, local=False):
        """
        Initialize with a :epkg:`JSON` data.

        @param  json_data       dictionary or string
        @param  width           (str) width
        @param  height          (str) height
        @param  divid           (str|None) id of the div
        @param  show_to_level   (int|None) show first level
        @param  local           (bool|False) use local javascript files

        If *local*, local javascript files are copied in the current folder.
        """
        if isinstance(json_data, (dict, list)):
            self.json_str = json.dumps(json_data)
        else:
            self.json_str = json
        self.uuid = divid if divid else str(uuid.uuid4())
        self.width = width
        self.height = height
        self.show_to_level = show_to_level
        self.local = local
        self._copy_local(local)

    def _copy_local(self, local):
        """
        If *self.local*, copies javascript dependencies in the local folder.
        """
        if not self.local:
            return
        if os.path.exists('renderjson.js'):
            # Already done.
            return
        this = os.path.dirname(__file__)
        js = os.path.join(this, '..', 'js', 'renderjson', 'renderjson.js')
        if not os.path.exists(js):
            raise FileNotFoundError("Unable to find '{0}'".format(js))
        dest = local if isinstance(local, str) else os.getcwd()
        shutil.copy(js, dest)

    def generate_html(self):
        """
        Overloads method
        `_ipython_display_ <http://ipython.readthedocs.io/en/stable/config/integrating.html?highlight=Integrating%20>`_.
        """
        level = " show_to_level={}".format(
            self.show_to_level) if self.show_to_level is not None else ''
        ht = '<div id="{}" style="height: {}; width:{};"{}></div>'.format(
            self.uuid, self.width, self.height, level)
        lib = 'renderjson.js' if self.local else 'https://rawgit.com/caldwell/renderjson/master/renderjson.js'
        js = """
        require(["%s"], function() {
        document.getElementById('%s').appendChild(renderjson(%s))
        }); """ % (lib, self.uuid, self.json_str)
        return ht, js


class RenderJSONObj(RenderJSONRaw):
    """
    Renders :epkg:`JSON` using :epkg:`javascript`.
    """

    def _ipython_display_(self):
        ht, js = self.generate_html()
        display_html(ht, raw=True)
        display_javascript(js, raw=True)


class RenderJSON(RenderJSONRaw):
    """
    Renders :epkg:`JSON` using :epkg:`javascript`, outputs only :epkg:`HTML`.
    """

    def _repr_html_(self):
        ht, js = self.generate_html()
        ht += "\n<script>\n{0}\n</script>\n".format(js)
        return ht


def JSONJS(data, only_html=True, show_to_level=None, local=False):
    """
    Inspired from `Pretty JSON Formatting in IPython Notebook <http://stackoverflow.com/questions/18873066/pretty-json-formatting-in-ipython-notebook>`_.

    @param      data            dictionary or json string
    @param      show_to_level   show first level
    @param      local           use local files
    @return                     @see cl RenderJSON

    The function uses library
    `renderjson <https://github.com/caldwell/renderjson>`_.
    It returns an object with overwrite method
    `_ipython_display_ <http://ipython.readthedocs.io/en/stable/config/integrating.html?highlight=Integrating%20>`_.
    If *local* is true, javascript dependency are copied in the local folder.

    .. faqref::
        :title: Persistent javascript in a conververted notebook

        After a couple of tries, it appears that it is more efficient to
        render the javascript inside a section ``<script>...</script>``
        when the notebook is converted to RST (*only_html=True*).
    """
    if only_html:
        return RenderJSON(data, show_to_level=show_to_level, local=local)
    else:
        return RenderJSONObj(data, show_to_level=show_to_level, local=local)
