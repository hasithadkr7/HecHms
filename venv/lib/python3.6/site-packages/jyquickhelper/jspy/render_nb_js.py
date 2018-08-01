# -*- coding: utf-8 -*-
"""
@file
@brief Helpers around JSON
"""
import sys
import uuid
import os
import shutil
from IPython.display import display_html, display_javascript

if sys.version_info[0] < 3:
    import urllib2 as liburl
else:
    import urllib.request as liburl
    import urllib.error as liberror


class UrlNotFoundError(Exception):
    """
    Raised when a url does not exist.
    """

    def __init__(self, url, code):
        Exception.__init__(
            self, "Url not found: returned code={0} for '{1}'".format(code, url))


class JavascriptScriptError(ValueError):
    """
    Raised when the class does not find what it expects.
    """
    pass


def check_url(url):
    if sys.version_info[0] < 3:
        ret = liburl.urlopen(url)
        if ret.code == 200:
            ret.close()
            return True
        else:
            raise UrlNotFoundError(url, ret.code)
    else:
        try:
            liburl.urlopen(url)
            return True
        except liberror.HTTPError as e:
            raise UrlNotFoundError(url, e.code)
        except liberror.URLError as e:
            raise UrlNotFoundError(url, e.reason)
        except Exception as e:
            raise Exception("Issue with url '{0}'".format(url)) from e


class RenderJSRaw(object):
    """
    Adds :epkg:`javascript` into a noteboook.
    """

    def __init__(self, script, width="100%", height="100%", divid=None, css=None,
                 libs=None, style=None, only_html=False, div_class=None, check_urls=True,
                 local=False):
        """
        @param  script          (str) script
        @param  width           (str) width
        @param  height          (str) height
        @param  style           (str) style (added in ``<style>...</style>``)
        @param  divid           (str|None) id of the div
        @param  css             (list) list of css
        @param  libs            (list) list of dependencies
        @param  only_html       (bool) use only function `display_html <http://ipython.readthedocs.io/en/stable/api/generated/IPython.display.html?highlight=display_html#IPython.display.display_html>`_
                                and not `display_javascript <http://ipython.readthedocs.io/en/stable/api/generated/IPython.display.html?highlight=display_html#IPython.display.display_javascript>`_ to add
                                javascript to the page.
        @param  div_class       (str) class of the section ``div`` which will host the results
                                of the javascript
        @param  check_urls      (bool) by default, check url exists
        @param  local           (bool|False) use local javascript files
        """
        self.script = script
        self.uuid = divid if divid else "M" + \
            str(uuid.uuid4()).replace("-", "")
        if style is None:
            style = ''
            if width is not None and 'width' not in style:
                style += "width:{0};".format(width)
            if height is not None and 'height' not in style:
                style += "height:{0};".format(height)
            if not style:
                style = None
        else:
            if width is not None and 'width' not in style:
                style += "width:{0};".format(width)
            if height is not None and 'height' not in style:
                style += "height:{0};".format(height)
        self.style = style
        self.only_html = only_html
        self.div_class = div_class
        if "__ID__" not in script:
            raise JavascriptScriptError(
                "The sript does not contain any string __ID__. It is replaced by the ID value in script:\n{0}".format(script))
        self.local = local
        self.css, self.libs = self._copy_local(css, libs, local)
        if check_urls and not local:
            if self.css is not None:
                for c in self.css:
                    check_url(c)
            if self.libs is not None:
                for l in self.libs:
                    if isinstance(l, dict):
                        check_url(l['path'])
                    else:
                        check_url(l)

    def _copy_local(self, css, libs, local):
        """
        If *self.local*, copies javascript dependencies in the local folder.

        @param      css     list of css
        @param      libs    list of libraries
        @param      local   boolean or new location
        @return             tuple (css, libs)
        """
        if not self.local:
            return css, libs
        to_copy = []
        if css:
            to_copy.extend(css)
        if libs:
            for js in libs:
                if isinstance(js, dict):
                    to_copy.append(js['path'])
                else:
                    to_copy.append(js)

        for js in to_copy:
            if not os.path.exists(js):
                raise FileNotFoundError("Unable to find '{0}'".format(js))
            dest = local if isinstance(local, str) else os.getcwd()
            shutil.copy(js, dest)

        if css:
            css = [os.path.split(c)[-1] for c in css]
        if libs:
            def proc(d):
                if isinstance(d, dict):
                    d = d.copy()
                    d['path'] = os.path.split(d['path'])[-1]
                    return d
                else:
                    return os.path.split(d)[-1]
            libs = [proc(c) for c in libs]
        return css, libs

    def generate_html(self):
        """
        Overloads method
        `_ipython_display_ <http://ipython.readthedocs.io/en/stable/config/integrating.html?highlight=Integrating%20>`_.

        @return     `HTML <http://ipython.readthedocs.io/en/stable/api/generated/IPython.display.html#IPython.display.HTML>`_ text,
                    `Javascript <http://ipython.readthedocs.io/en/stable/api/generated/IPython.display.html#IPython.display.Javascript>`_ text
        """
        if self.style:
            style = ' style="{0}"'.format(self.style)
        else:
            style = ""
        if self.div_class:
            divcl = ' class="{0}"'.format(self.div_class)
        else:
            divcl = ""
        if self.css:
            css = "".join(
                '<link rel="stylesheet" href="{0}" type="text/css" />'.format(c) for c in self.css)
            ht = '<div id="{uuid}-css">{css}<div{divcl} id="{uuid}"{style}></div></div>'.format(
                uuid=self.uuid, css=css, style=style, divcl=divcl)
        else:
            ht = '<div id="{uuid}-cont"><div{divcl} id="{uuid}"{style}></div></div>'.format(
                uuid=self.uuid, style=style, divcl=divcl)

        script = self.script.replace("__ID__", self.uuid)
        if self.libs:
            names = []
            paths = []
            shims = {}
            args = []
            exports = []
            for l in self.libs:
                if isinstance(l, dict):
                    name = l.get("name", None)
                    if "path" in l:
                        p = l["path"]
                        if name is None:
                            name = ".".join((p.split("/")[-1]).split(".")[:-1])
                        path = ".".join(p.split(".")[:-1])
                        paths.append((name, path))
                    else:
                        raise KeyError(
                            "unable to find 'path' in {0}".format(l))
                    names.append(name)
                    args.append(name)
                    if "exports" in l:
                        if name not in shims:
                            shims[name] = {}
                        shims[name]["exports"] = l["exports"]
                        if isinstance(l["exports"], list):
                            exports.extend(l["exports"])
                        else:
                            exports.append(l["exports"])
                    if "deps" in l:
                        if name not in shims:
                            shims[name] = {}
                        shims[name]["deps"] = l["deps"]
                else:
                    names.append(l)
            if len(names) == 0:
                raise ValueError("names is empty.\nlibs={0}\npaths={1}\nshims={2}\nexports={3}".format(self.libs,
                                                                                                       paths, shims, exports))
            require = ",".join("'{0}'".format(l) for l in names)

            config = ["require.config({"]
            if len(paths) > 0:
                config.append("paths:{")
                for name, path in paths:
                    config.append("'{0}':'{1}',".format(name, path))
                config.append("},")
            if len(shims) > 0:
                config.append("shim:{")

                def vd(d):
                    rows = []
                    for k, v in sorted(d.items()):
                        rows.append("'{0}':{1}".format(
                            k, v if isinstance(v, list) else "'{0}'".format(v)))
                    return "{%s}" % ",".join(rows)
                for k, v in sorted(shims.items()):
                    config.append("'{0}':{1},".format(k, vd(v)))
                config.append("},")
            config.append("});")
            if len(config) > 2:
                prefix = "\n".join(config) + "\n"
            else:
                prefix = ""
            js = prefix + \
                """\nrequire([%s], function(%s) { %s });\n""" % (
                    require, ",".join(args), script)
        else:
            js = script
        if self.only_html:
            ht += "\n<script>\n%s\n</script>" % js
            return ht, None
        else:
            return ht, js


class RenderJSObj(RenderJSRaw):
    """
    Renders JS using :epkg:`javascript`.
    """

    def _ipython_display_(self):
        """
        overloads method
        `_ipython_display_ <http://ipython.readthedocs.io/en/stable/config/integrating.html?highlight=Integrating%20>`_.
        """
        ht, js = self.generate_html()
        if js is None:
            display_html(ht, raw=True)
        else:
            display_html(ht, raw=True)
            display_javascript(js, raw=True)


class RenderJS(RenderJSRaw):
    """
    Renders :epkg:`javascript`, only outputs :epkg:`HTML`.
    """

    def _repr_html_(self):
        """
        Overloads method *_repr_html_*.
        """
        ht, js = self.generate_html()
        if js is not None:
            ht += "\n<script>\n{0}\n</script>\n".format(js)
        return ht
