import json
import os
from unittest import TestCase


class TestCase(TestCase):
    def load_fixture(self, path, json=False, lines=False):
        base_path = os.path.realpath(os.path.dirname(__file__))
        path = os.path.join(base_path, 'fixtures', path)
        with open(path, 'r') as f:
            if lines:
                return f.readlines()
            contents = f.read()

        if json:
            return json.loads(contents)
        return contents
