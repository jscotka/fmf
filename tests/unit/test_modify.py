# coding: utf-8

from __future__ import unicode_literals, absolute_import

import unittest
import os
import tempfile
from fmf.base import Tree
from shutil import rmtree, copytree

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Constants
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Prepare path to examples
PATH = os.path.dirname(os.path.realpath(__file__))
EXAMPLES = PATH + "/../../examples/"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Tree
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestModify(unittest.TestCase):
    """ Tree class """

    def setUp(self):
        self.wget_path = EXAMPLES + "wget"
        self.tempdir = tempfile.mktemp()
        copytree(self.wget_path, self.tempdir)
        self.wget = Tree(self.tempdir)

    def tearDown(self):
        rmtree(self.tempdir)

    def test_inheritance(self):
        """ Inheritance and data types """
        item = self.wget.find('/recursion/deep')
        item.modify(dict(depth = 2000, new = "some"))
        item.parent.modify(dict(parent_attr = "value"))

        # reload the data
        self.wget = Tree(self.tempdir)
        item = self.wget.find('/recursion/deep')

        self.assertEqual(item.data['tags'], ['Tier2'])
        self.assertEqual(item.parent.data['tags'], ['Tier2'])
        self.assertEqual(item.data['depth'], 2000)
        self.assertIn('depth', item.data)
        self.assertNotIn('depth', item.parent.data)
        self.assertEqual(item.data['new'], "some")
        self.assertEqual(item.data['parent_attr'], "value")


    def test_deep_modify(self):
        req = self.wget.find('/requirements')
        proto = self.wget.find('/requirements/protocols')
        ftp = self.wget.find('/requirements/protocols/ftp')

        req.modify(dict(new="some"))
        proto.modify(dict(coverage="changed", new_attr="val"))
        ftp.modify(dict(server="vsftpd"))

        self.wget = Tree(self.tempdir)
        req = self.wget.find('/requirements')
        proto = self.wget.find('/requirements/protocols')
        ftp = self.wget.find('/requirements/protocols/ftp')
        self.assertEqual(req.data["new"], "some")
        self.assertEqual(proto.data["new"], "some")
        self.assertEqual(ftp.data["new"], "some")
        self.assertNotIn("server",proto.data)
        self.assertIn("server", ftp.data)

        self.assertNotIn("new_attr", req.data)
        self.assertIn("new_attr", proto.data)
        self.assertIn("new_attr", ftp.data)
        self.assertEqual(proto.data["coverage"], "changed")
