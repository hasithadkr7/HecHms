# -*- coding: utf-8 -*-
"""
Main files, contains the version, the url to the documention.
"""

__version__ = "1.5"
__author__ = "Xavier Dupré"
__github__ = "https://github.com/sdpython/tkinterquickhelper"
__url__ = "http://www.xavierdupre.fr/app/tkinterquickhelper/helpsphinx/index.html"
__license__ = "MIT License"
__blog__ = """
<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
    <head>
        <title>blog</title>
    </head>
    <body>
        <outline text="tkinterquickhelper"
            title="tkinterquickhelper"
            type="rss"
            xmlUrl="http://www.xavierdupre.fr/app/tkinterquickhelper/helpsphinx/_downloads/rss.xml"
            htmlUrl="http://www.xavierdupre.fr/app/tkinterquickhelper/helpsphinx/blog/main_0000.html" />
    </body>
</opml>
"""


def check():
    """
    Checks the library is working.
    It raises an exception if it does not.

    @return         boolean
    """
    from .funcwin import check_icon
    from pyquickhelper.loghelper import check_log
    check_icon()
    check_log()
    return True


def _setup_hook(add_print=False, unit_test=False):
    """
    if this function is added to the module,
    the help automation and unit tests call it first before
    anything goes on as an initialization step.
    It should be run in a separate process.

    @param      add_print       print *Success: _setup_hook*
    @param      unit_test       used only for unit testing purpose
    """
    # we can check many things, needed module
    # any others things before unit tests are started
    if add_print:
        print("Success: _setup_hook")
