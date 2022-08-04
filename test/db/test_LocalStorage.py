import json
import os
import shutil
from unittest import TestCase

from db.LocalStorage import LocalStorage
from utils.nested_dict import deep_read


class TestLocalStorage(TestCase):
    PATH = "debug/unittest"
    STORAGE = LocalStorage()
    STORAGE.PATH = PATH

    @classmethod
    def setUpClass(cls) -> None:
        if os.path.exists(cls.PATH):
            shutil.rmtree(cls.PATH)
        os.mkdir(cls.PATH)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(f"{cls.PATH}/STORAGE.json"):
            os.remove(f"{cls.PATH}/STORAGE.json")

        if os.path.exists(cls.PATH):
            shutil.rmtree(cls.PATH)

    def test_load(self):
        saved = {
            "a": 1,
            "b": {
                "c": "cat",
                "d": {
                    "e": True
                }
            }
        }

        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as f:
            f.write(json.dumps(saved))

        self.STORAGE.load()
        self.assertEqual(saved, self.STORAGE.JSON)

    def test_write(self):
        self.STORAGE.JSON = {
            "a": 1,
            "b": {
                "c": "cat",
                "d": {
                    "e": True
                }
            }
        }

        self.STORAGE.write(42, "b/d/f")
        self.assertEqual(42, deep_read(self.STORAGE.JSON, "b/d/f".split('/')))

        self.STORAGE.REL += "b/d"
        self.STORAGE.REL_PATH.extend(["b", "d"])
        self.STORAGE.write(None, "g/h")
        print(self.STORAGE.JSON)
        self.assertEqual(
            None, deep_read(self.STORAGE.JSON, "b/d/g/h".split('/'))
        )
        self.STORAGE.REL = ""
        self.STORAGE.REL_PATH = []

    def test_read(self):
        self.STORAGE.JSON = {
            "a": 1,
            "b": {
                "c": "cat",
                "d": {
                    "e": True
                }
            }
        }

        self.assertEqual(True, self.STORAGE.read("b/d/e"))
        with self.assertRaises(ValueError):
            self.STORAGE.read("b/d/e/f")

    def test_exists(self):
        self.STORAGE.JSON = {
            "a": 1,
            "b": {
                "c": "cat",
                "d": {
                    "e": True
                }
            }
        }

        self.assertTrue(self.STORAGE.exists("b/d"))
        self.assertFalse(self.STORAGE.exists("b/skjdf"))

    def test_delete(self):
        self.STORAGE.JSON = {
            "a": 1,
            "b": {
                "c": "cat",
                "d": {
                    "e": True
                }
            }
        }
        self.assertTrue(self.STORAGE.exists("b"))
        self.STORAGE.delete("b")
        self.assertFalse(self.STORAGE.exists("b"))

    def test_is_empty(self):
        self.STORAGE.JSON = {
            "a": 1,
            "b": {
                "c": "cat",
                "d": {
                    "e": {}
                }
            }
        }

        self.assertTrue(self.STORAGE.is_empty("b/d/e"))
        self.assertFalse(self.STORAGE.is_empty("a"))

    def test_make(self):
        self.STORAGE.JSON = {
            "a": 1,
            "b": {
                "c": "cat",
                "d": {
                    "e": True
                }
            }
        }

        self.assertFalse(self.STORAGE.exists("b/d/f"))
        self.STORAGE.make("b/d/f")
        self.assertTrue(self.STORAGE.exists("b/d/f"))
        self.assertTrue(self.STORAGE.is_empty("b/d/f"))

    def test_list_nodes(self):
        self.STORAGE.JSON = {
            "a": 1,
            "b": {
                "c": "cat",
                "d": {
                    "e": True
                }
            }
        }

        self.assertEqual(["a", "b"], self.STORAGE.list_nodes())
        self.assertEqual([], self.STORAGE.list_nodes("b/d/e"))

    def test_reset(self):
        self.STORAGE.JSON = {
            "a": 1,
            "b": {
                "c": "cat",
                "d": {
                    "e": True
                }
            }
        }

        self.STORAGE.reset()
        self.assertEqual({}, self.STORAGE.JSON)

    def test_save(self):
        self.STORAGE.JSON = {
            "a": 1,
            "b": {
                "c": "cat",
                "d": {
                    "e": True
                }
            }
        }

        self.STORAGE.write({"g": [1, 2, 3]}, "b/d/f")
        self.STORAGE.save()
        self.assertEqual({
            "a": 1,
            "b": {
                "c": "cat",
                "d": {
                    "e": True,
                    "f": {
                        "g": [1, 2, 3]
                    }
                }
            }
        }, self.STORAGE.JSON)

        new_storage = LocalStorage()
        new_storage.PATH = self.PATH
        new_storage.load()

        self.assertEqual(self.STORAGE.JSON, new_storage.JSON)

    def test_change_root(self):
        self.STORAGE.reset()
        self.assertEqual({}, self.STORAGE.read())

        self.STORAGE.write("test", "a/b/c")

        self.assertEqual({
            'a': {
                'b': {
                    'c': 'test'
                }
            }
        }, self.STORAGE.JSON)
        self.assertEqual("test", self.STORAGE.read("a/b/c"))

        json_i = self.STORAGE.JSON
        self.STORAGE.change_ref("a/b")
        json_f = self.STORAGE.JSON

        self.assertEqual(json_i, json_f)
        self.assertEqual(["c"], self.STORAGE.list_nodes())
        self.assertEqual("test", self.STORAGE.read("c"))

        self.STORAGE.write(42, "d/e")
        self.assertEqual(["c", "d"], self.STORAGE.list_nodes())
        self.assertEqual(42, self.STORAGE.read("d/e"))

        json_i = self.STORAGE.JSON
        self.STORAGE.change_ref("d")
        json_f = self.STORAGE.JSON

        self.assertEqual(json_i, json_f)
        self.assertEqual(["e"], self.STORAGE.list_nodes())
        self.assertEqual(42, self.STORAGE.read("e"))

        json_i = self.STORAGE.JSON
        self.STORAGE.change_ref("", reset=True)
        json_f = self.STORAGE.JSON

        self.assertEqual(json_i, json_f)
        self.STORAGE.save()
