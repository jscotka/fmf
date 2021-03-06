# coding: utf-8

from __future__ import unicode_literals, absolute_import

import os
import pytest
from fmf.utils import FileError, MergeError
from fmf.base import Tree


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Constants
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Prepare path to examples
PATH = os.path.dirname(os.path.realpath(__file__))
WGET = PATH + "/../examples/wget"
MERGE = PATH + "/../examples/merge"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Tree
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestTree(object):
    """ Tree class """

    def setup_method(self):
        """ Load examples """
        self.wget = Tree(WGET)
        self.merge = Tree(MERGE)

    def test_basic(self):
        """ No directory path given """
        with pytest.raises(FileError):
            Tree("")

    def test_hidden(self):
        """ Hidden files and directories """
        assert(".hidden" not in self.wget.children)

    def test_inheritance(self):
        """ Inheritance and data types """
        deep = self.wget.find('wget/recursion/deep')
        assert(deep.data['depth'] == 1000)
        assert(deep.data['description'] == 'Check recursive download options')
        assert(deep.data['tags'] == ['Tier2'])

    def test_merge(self):
        """ Attribute merging """
        child = self.merge.find('merge/parent/child')
        assert('General' in child.data['description'])
        assert('Specific' in child.data['description'])
        assert(child.data['tags'] == ['Tier1', 'Tier2'])
        assert(child.data['time'] == 15)
        assert('time+' not in child.data)
        with pytest.raises(MergeError):
            child.update({"time+": "string"})

    def test_get(self):
        """ Get attributes """
        assert(isinstance(self.wget.get(), dict))
        assert('Petr' in self.wget.get('tester'))

    def test_show(self):
        """ Show metadata """
        assert(isinstance(self.wget.show(brief=True), type("")))
        assert(isinstance(self.wget.show(), type("")))
        assert('wget' in self.wget.show())

    def test_update(self):
        """ Update data """
        data = self.wget.get()
        self.wget.update(None)
        assert(self.wget.data == data)

    def test_find(self):
        """ Find node by name """
        assert(self.wget.find("non-existent") == None)
