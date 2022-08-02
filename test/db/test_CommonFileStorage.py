import os
import shutil
from unittest import TestCase

from db.CommonFileStorage import CommonFileStorage


class TestCommonFileStorage(TestCase):
    PATH = "debug/unittest"
    FS = CommonFileStorage(PATH)

    @classmethod
    def setUpClass(cls) -> None:
        if os.path.exists(cls.PATH):
            shutil.rmtree(cls.PATH)
        os.mkdir(cls.PATH)

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(cls.PATH):
            shutil.rmtree(cls.PATH)

    def test_init(self):
        self.assertEqual(self.FS.ROOT, self.PATH)
        self.assertTrue(os.path.exists(self.PATH))

    def test_write(self):
        self.FS.write(path="test", data="test")
        with open(f"{self.PATH}/test", 'r', encoding="utf-8") as f:
            data = f.read()

        self.assertEqual(data, "test")

    def test_read(self):
        self.FS.write("test", "test")
        data = self.FS.read("test")

        self.assertEqual(data, "test")

    def test_create_folder(self):
        self.FS.create_folder("test")

        self.assertTrue(os.path.exists(f"{self.PATH}/test"))
        self.assertTrue(os.path.isdir(f"{self.PATH}/test"))

        shutil.rmtree(f"{self.PATH}/test")

    def test_delete_folder(self):
        self.FS.create_folder("test")
        self.FS.create_folder("test/subtest")
        self.FS.write("test/testfile", "test")

        self.assertEqual(sorted(["testfile", "subtest"]),
                         sorted(os.listdir(f"{self.PATH}/test")))

        self.FS.delete_folder("test")

        self.assertEqual([], sorted(os.listdir(f"{self.PATH}")))

    def test_delete_file(self):
        self.FS.write("testfile", "test")
        self.FS.delete_file("testfile")

        self.assertFalse(os.path.exists(f"{self.PATH}/testfile"))

    def test_list_files(self):
        self.FS.create_folder("testfolder")
        self.FS.write("testfolder/testfile1", "test")
        self.FS.write("testfolder/testfile2", "test")
        self.FS.write("testfolder/testfile3", "test")
        self.FS.write("testfolder/testfile4", "test")

        self.assertEqual(
            sorted(["testfile1", "testfile2", "testfile3", "testfile4"]),
            sorted(self.FS.list_files("testfolder")))

        self.FS.delete_folder("testfolder")

    def test_file_exists(self):
        self.FS.write("test1", "test")
        self.assertTrue(self.FS.file_exists("test1"))
        self.FS.delete_file("test1")

    def test_folder_exists(self):
        self.FS.create_folder("testfolder")
        self.assertTrue(self.FS.folder_exists("testfolder"))
        self.FS.delete_folder("testfolder")

    def test_is_file(self):
        self.FS.write("test2", "test")
        self.assertTrue(self.FS.is_file("test2"))
        self.FS.delete_file("test2")

    def test_is_folder(self):
        self.FS.create_folder("testfolder2")
        self.assertTrue(self.FS.is_folder("testfolder2"))
        self.FS.delete_folder("testfolder2")

    def test_file_empty(self):
        self.FS.write("test3", "")
        self.assertTrue(self.FS.file_empty("test3"))
        self.FS.delete_file("test3")

    def test_folder_empty(self):
        self.FS.create_folder("testfolder2")
        self.assertTrue(self.FS.folder_empty("testfolder2"))
        self.FS.delete_folder("testfolder2")
