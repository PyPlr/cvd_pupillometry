# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 12:01:22 2020

@author: JTM
"""


import unittest

import pyplr

class TestSum(unittest.TestCase):
    def test_list_int(self):
        """
        Test that it can sum a list of integers
        """
        data = [1, 2, 3]
        result = sum(data)
        self.assertEqual(result, 6)

if __name__ == '__main__':
    unittest.main()
