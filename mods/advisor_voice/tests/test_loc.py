import struct
import unittest

from game_files import read_loc


def loc(rows):
    raw = bytearray(b'\xff\xfeLOC\0' + struct.pack('<II', 1, len(rows)))
    for key, value, flag in rows:
        for text in (key, value):
            encoded = text.encode('utf-16-le')
            raw += struct.pack('<H', len(encoded) // 2) + encoded
        raw += bytes([flag])
    return bytes(raw)


class LocTests(unittest.TestCase):
    def test_chinese_and_surrogate_pair_preserve_markup(self):
        text = '测试字幕 [[col:red]]火🔥[[/col]]\n{NAME}'
        self.assertEqual(read_loc(loc([('key', text, 1)])), {'key': text})

    def test_duplicate_and_invalid_flag(self):
        for rows in ([('key', 'a', 0), ('key', 'b', 0)], [('key', 'a', 2)]):
            with self.assertRaises(ValueError):
                read_loc(loc(rows))

    def test_truncation_and_trailing_bytes(self):
        raw = loc([('key', '字幕', 0)])
        for bad in (raw[:-1], raw + b'x'):
            with self.assertRaises(ValueError):
                read_loc(bad)
