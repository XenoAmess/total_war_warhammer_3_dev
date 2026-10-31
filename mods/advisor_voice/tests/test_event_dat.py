import unittest
import struct
import event_dat

class TestEventDat(unittest.TestCase):
    def test_empty_file(self):
        # 24 zero bytes: 6 sections with count 0
        data = b'\x00' * 24
        result = event_dat.parse_dat(data)
        self.assertEqual(result.events, ())
        self.assertEqual(result.state_groups_0, ())
        self.assertEqual(result.state_groups_1, ())
        self.assertEqual(result.dialogue_events, ())
        self.assertEqual(result.settings, ())
        self.assertEqual(result.unknown, ())

    def test_non_empty_fields(self):
        # Construct expected binary data manually
        # Section 0: EventWithStateGroup (1 item)
        #   Event: "\u987e\u95ee", Value: 1.0
        # Section 1: StateGroupsWithStates0 (1 item)
        #   StateGroup: "group0", States: ["state1", "state2"]
        # Section 2: StateGroupsWithStates1 (1 item)
        #   StateGroup: "group1", States: ["state3"]
        # Section 3: DialogueEventsWithStateGroups (1 item)
        #   Event: "dialogue", StateGroups: [100, 200]
        # Section 4: SettingValues (1 item)
        #   Event: "setting", MinValue: 0.0, MaxValue: 1.0
        # Section 5: Unknown (1 item)
        #   "unknown_str"

        def write_str32(s):
            encoded = s.encode('utf-8')
            return struct.pack('<i', len(encoded)) + encoded

        def write_float(f):
            return struct.pack('<f', f)

        def write_uint32(u):
            return struct.pack('<I', u)

        def write_int32(i):
            return struct.pack('<i', i)

        # Section 0
        sec0 = write_int32(1) + write_str32("\u987e\u95ee") + write_float(1.0)
        # Section 1
        sec1 = write_int32(1) + write_str32("group0") + write_uint32(2) + write_str32("state1") + write_str32("state2")
        # Section 2
        sec2 = write_int32(1) + write_str32("group1") + write_uint32(1) + write_str32("state3")
        # Section 3
        sec3 = write_int32(1) + write_str32("dialogue") + write_uint32(2) + write_uint32(100) + write_uint32(200)
        # Section 4
        sec4 = write_int32(1) + write_str32("setting") + write_float(0.0) + write_float(1.0)
        # Section 5
        sec5 = write_int32(1) + write_str32("unknown_str")

        data = sec0 + sec1 + sec2 + sec3 + sec4 + sec5
        result = event_dat.parse_dat(data)

        self.assertEqual(len(result.events), 1)
        self.assertEqual(result.events[0].name, "\u987e\u95ee")
        self.assertEqual(result.events[0].value, 1.0)

        self.assertEqual(len(result.state_groups_0), 1)
        self.assertEqual(result.state_groups_0[0].name, "group0")
        self.assertEqual(result.state_groups_0[0].states, ("state1", "state2"))

        self.assertEqual(len(result.state_groups_1), 1)
        self.assertEqual(result.state_groups_1[0].name, "group1")
        self.assertEqual(result.state_groups_1[0].states, ("state3",))

        self.assertEqual(len(result.dialogue_events), 1)
        self.assertEqual(result.dialogue_events[0].name, "dialogue")
        self.assertEqual(result.dialogue_events[0].groups, (100, 200))

        self.assertEqual(len(result.settings), 1)
        self.assertEqual(result.settings[0].name, "setting")
        self.assertEqual(result.settings[0].minimum, 0.0)
        self.assertEqual(result.settings[0].maximum, 1.0)

        self.assertEqual(len(result.unknown), 1)
        self.assertEqual(result.unknown[0], "unknown_str")

    def test_truncated(self):
        # Truncate after section 0 count
        data = struct.pack('<i', 1) + b'\x00' * 10
        with self.assertRaises(ValueError):
            event_dat.parse_dat(data)

    def test_invalid_utf8(self):
        # Invalid UTF-8 in string
        def write_str32(s):
            encoded = s.encode('utf-8')
            return struct.pack('<i', len(encoded)) + encoded

        # Section 0 with invalid UTF-8
        sec0 = struct.pack('<i', 1) + struct.pack('<i', 5) + b'\xff\xff\xff\xff\xff' + struct.pack('<f', 1.0)
        # Other sections empty
        sec1 = struct.pack('<i', 0)
        sec2 = struct.pack('<i', 0)
        sec3 = struct.pack('<i', 0)
        sec4 = struct.pack('<i', 0)
        sec5 = struct.pack('<i', 0)

        data = sec0 + sec1 + sec2 + sec3 + sec4 + sec5
        with self.assertRaises(ValueError):
            event_dat.parse_dat(data)

    def test_huge_count(self):
        # Huge count in section 0
        data = struct.pack('<i', 1000000) + b'\x00' * 100
        with self.assertRaises(ValueError):
            event_dat.parse_dat(data)

    def test_trailing_garbage(self):
        # Valid data plus trailing garbage
        def write_str32(s):
            encoded = s.encode('utf-8')
            return struct.pack('<i', len(encoded)) + encoded

        def write_float(f):
            return struct.pack('<f', f)

        def write_uint32(u):
            return struct.pack('<I', u)

        def write_int32(i):
            return struct.pack('<i', i)

        # Section 0
        sec0 = write_int32(1) + write_str32("\u987e\u95ee") + write_float(1.0)
        # Section 1
        sec1 = write_int32(1) + write_str32("group0") + write_uint32(2) + write_str32("state1") + write_str32("state2")
        # Section 2
        sec2 = write_int32(1) + write_str32("group1") + write_uint32(1) + write_str32("state3")
        # Section 3
        sec3 = write_int32(1) + write_str32("dialogue") + write_uint32(2) + write_uint32(100) + write_uint32(200)
        # Section 4
        sec4 = write_int32(1) + write_str32("setting") + write_float(0.0) + write_float(1.0)
        # Section 5
        sec5 = write_int32(1) + write_str32("unknown_str")

        data = sec0 + sec1 + sec2 + sec3 + sec4 + sec5 + b'\x00' * 10
        with self.assertRaises(ValueError):
            event_dat.parse_dat(data)

if __name__ == '__main__':
    unittest.main()
