from unittest import TestCase

from utils.nested_dict import deep_write, deep_read, deep_delete


class TestNestedDict(TestCase):
    def test_deep_write(self):
        d = {
            "a": 1,
            "b": {
                "c": 2,
                "d": {
                    "e": 3
                }
            }
        }

        deep_write(d, 4, ["b", "d", "f"])
        self.assertTrue(d["b"]["d"]["f"] == 4)

        deep_write(d, 5, ["g"])
        self.assertTrue(d["g"] == 5)

        with self.assertRaises(ValueError):
            deep_write(d, 5, ["b", "c", "g"])

    def test_deep_read(self):
        d = {
            "a": 1,
            "b": {
                "c": 2,
                "d": {
                    "e": 3
                }
            }
        }

        self.assertEqual(deep_read(d, ["b", "d", "e"]), 3)

        with self.assertRaises(ValueError):
            deep_read(d, ["a", "d", "e"])
            deep_read(d, ["c"])

    def test_deep_delete(self):
        d = {
            "a": 1,
            "b": {
                "c": 2,
                "d": {
                    "e": 3
                }
            }
        }

        self.assertIsNotNone(d.get("b").get("d").get("e"), None)
        deep_delete(d, ["b", "d", "e"])
        self.assertIsNone(d.get("b").get("d").get("e"), None)

        with self.assertRaises(ValueError):
            deep_delete(d, ["a", "d", "e"])
            deep_delete(d, ["c"])

        deep_delete(d, ["b"])
        self.assertEqual(["a"], list(d.keys()))
