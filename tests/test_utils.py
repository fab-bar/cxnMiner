from unittest import mock

import pytest

from cxnminer.utils.helpers import open_file

@mock.patch('builtins.open')
def test_open_file(mockfunction):

    filename = 'test.txt'

    open_file(filename)
    mockfunction.assert_called_with(filename, 'r', encoding='utf-8')

@mock.patch('gzip.open')
def test_open_zipped_file(mockfunction):

    filename = 'test.txt.gz'

    open_file(filename)
    mockfunction.assert_called_with(filename, 'rt', encoding='utf-8')
