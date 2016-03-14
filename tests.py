import unittest

from pgindexrebuild import size_pretty

class SizePrettyTestCase(unittest.TestCase):

    def _test(num, expected_output):
        def test(self):
            actual_output = size_pretty(num)
            self.assertEqual(expected_output, actual_output)
        test.__doc__ = "size_pretty({}) should give {!r}".format(num, expected_output)

        return test

    test_size1 = _test(1, "1B")
    test_size2 = _test(1024, "1.0KiB")
    test_size3 = _test(1024*1024, "1.0MiB")
    test_size4 = _test(1024*1024*1024, "1.0GiB")
    test_size5 = _test(-1024*1024*1024, "-1.0GiB")


if __name__ == '__main__':
    unittest.main()
