"""Contract cases derived from local-model tests, with corrected fixtures."""
import hashlib
import struct
import unittest

from wem import inspect_wem


FMT = struct.pack('<HHIIHH', 65535, 1, 48000, 10000, 0, 0)


def riff(chunks, pad_final=True):
    body = bytearray(b'WAVE')
    for index, (tag, value) in enumerate(chunks):
        body += tag + struct.pack('<I', len(value)) + value
        if len(value) % 2 and (pad_final or index != len(chunks) - 1):
            body += b'\0'
    return b'RIFF' + struct.pack('<I', len(body)) + body


class WemTests(unittest.TestCase):
    def test_final_odd_payload_with_and_without_pad(self):
        for padded in (False, True):
            info = inspect_wem(riff([(b'fmt ', FMT), (b'data', b'123')], padded))
            self.assertEqual((info.codec, info.channels, info.sample_rate), (65535, 1, 48000))

    def test_ancillary_padding_and_chunk_order(self):
        raw = riff([(b'JUNK', b'x'), (b'data', b'ab'), (b'fmt ', FMT)])
        self.assertEqual(inspect_wem(raw).format_signature, hashlib.sha256(FMT).hexdigest())

    def test_full_format_setup_affects_signature(self):
        first = inspect_wem(riff([(b'fmt ', FMT + b'aa'), (b'data', b'ab')]))
        second = inspect_wem(riff([(b'fmt ', FMT + b'bb'), (b'data', b'ab')]))
        self.assertNotEqual(first.format_signature, second.format_signature)

    def test_duplicate_missing_short_empty_chunks(self):
        for chunks in ([(b'data', b'a')], [(b'fmt ', FMT)],
                       [(b'fmt ', FMT)] * 2 + [(b'data', b'a')],
                       [(b'fmt ', FMT), (b'data', b'a'), (b'data', b'b')],
                       [(b'fmt ', FMT[:15]), (b'data', b'a')],
                       [(b'fmt ', FMT), (b'data', b'')]):
            with self.subTest(chunks=chunks), self.assertRaises(ValueError):
                inspect_wem(riff(chunks))

    def test_truncation_after_valid_riff_size(self):
        raw = riff([(b'fmt ', FMT), (b'data', b'abc')])
        for length in (13, 18, 25, 38, 44):
            truncated = raw[:length]
            truncated = truncated[:4] + struct.pack('<I', len(truncated) - 8) + truncated[8:]
            with self.subTest(length=length), self.assertRaises(ValueError):
                inspect_wem(truncated)

    def test_invalid_headers_and_zero_format(self):
        raw = riff([(b'fmt ', FMT), (b'data', b'ab')])
        bad = [b'', raw[:10], b'RIFX' + raw[4:], raw + b'x', raw[:8] + b'FAIL' + raw[12:]]
        for channels, rate in ((0, 48000), (1, 0)):
            fmt = struct.pack('<HHIIHH', 65535, channels, rate, 10000, 0, 0)
            bad.append(riff([(b'fmt ', fmt), (b'data', b'ab')]))
        for value in bad:
            with self.subTest(raw=value), self.assertRaises(ValueError):
                inspect_wem(value)
