import os
import unittest
import cytoplasm
from cytoplasm.test_build import Base


test_site = os.path.join(os.path.dirname(__file__), "test")


class TestBlogController(Base):
    def setUp(self):
        Base.setUp(self, test_site)


if __name__ == '__main__':
    unittest.main()
