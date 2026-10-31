import unittest
from text_links import build_index, find_event_text, TextRef, EventTextMatch

class TestTextLinks(unittest.TestCase):
    def test_chinese_roundtrip(self):
        loc = {"aide_de_camp_speeches_text_测试字幕": "你好"}
        index = build_index(loc)
        matches = find_event_text("测试字幕", index)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].ref.key, "aide_de_camp_speeches_text_测试字幕")
        self.assertEqual(matches[0].ref.text, "你好")
        self.assertEqual(matches[0].method, "exact_event")

    def test_all5families(self):
        loc = {
            "aide_de_camp_speeches_text_evt": "a",
            "scripted_subtitles_localised_text_evt": "b",
            "vo_speech_texts_text_evt": "c",
            "pre_battle_speeches_text_evt": "d",
            "vo_fmv_texts_text_evt": "e"
        }
        index = build_index(loc)
        matches = find_event_text("evt", index)
        self.assertEqual(len(matches), 5)
        keys = sorted([m.ref.key for m in matches])
        self.assertEqual(keys, sorted(loc.keys()))
        for m in matches:
            self.assertEqual(m.method, "exact_event")

    def test_case_preserving_conflicts(self):
        loc = {
            "aide_de_camp_speeches_text_evt": "lower",
            "AIDE_DE_CAMP_SPEECHES_TEXT_EVT": "upper"
        }
        index = build_index(loc)
        matches = find_event_text("evt", index)
        self.assertEqual(len(matches), 2)
        keys = sorted([m.ref.key for m in matches])
        self.assertEqual(keys, ["AIDE_DE_CAMP_SPEECHES_TEXT_EVT", "aide_de_camp_speeches_text_evt"])
        texts = {m.ref.key: m.ref.text for m in matches}
        self.assertEqual(texts["aide_de_camp_speeches_text_evt"], "lower")
        self.assertEqual(texts["AIDE_DE_CAMP_SPEECHES_TEXT_EVT"], "upper")

    def test_exact_vs_wrapper_priority(self):
        loc = {
            "aide_de_camp_speeches_text_evt": "exact",
            "aide_de_camp_speeches_text_evt_1": "wrapper"
        }
        index = build_index(loc)
        matches = find_event_text("evt", index)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].ref.key, "aide_de_camp_speeches_text_evt")
        self.assertEqual(matches[0].method, "exact_event")

    def test_no_suffix2_stripping(self):
        loc = {
            "aide_de_camp_speeches_text_evt": "base"
        }
        index = build_index(loc)
        matches = find_event_text("evt_2", index)
        self.assertEqual(len(matches), 0)

    def test_no_substring_fuzzy(self):
        loc = {
            "aide_de_camp_speeches_text_evt_extra": "extra",
            "aide_de_camp_speeches_text_evt": "exact"
        }
        index = build_index(loc)
        matches = find_event_text("evt", index)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].ref.key, "aide_de_camp_speeches_text_evt")

    def test_unrelated_keys(self):
        loc = {
            "some_other_prefix_evt": "unrelated"
        }
        index = build_index(loc)
        matches = find_event_text("evt", index)
        self.assertEqual(len(matches), 0)

    def test_empty_text_retention(self):
        loc = {
            "aide_de_camp_speeches_text_evt": ""
        }
        index = build_index(loc)
        matches = find_event_text("evt", index)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].ref.text, "")
        self.assertEqual(matches[0].method, "exact_event")

    def test_empty_event(self):
        loc = {
            "aide_de_camp_speeches_text_": "empty_key"
        }
        index = build_index(loc)
        matches = find_event_text("", index)
        self.assertEqual(len(matches), 0)

    def test_play_prefix_removal(self):
        loc = {
            "aide_de_camp_speeches_text_evt": "exact",
            "aide_de_camp_speeches_text_play_evt": "play"
        }
        index = build_index(loc)
        matches = find_event_text("play_evt", index)
        self.assertEqual({m.ref.key: m.method for m in matches}, {
            "aide_de_camp_speeches_text_play_evt": "exact_event",
            "aide_de_camp_speeches_text_evt": "without_play"
        })

    def test_level_1_wrapper(self):
        loc = {
            "aide_de_camp_speeches_text_evt": "wrapper"
        }
        index = build_index(loc)
        matches = find_event_text("evt_1", index)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].ref.key, "aide_de_camp_speeches_text_evt")
        self.assertEqual(matches[0].method, "level_1_wrapper")

    def test_dedup_first_method(self):
        loc = {
            "aide_de_camp_speeches_text_evt": "exact",
            "aide_de_camp_speeches_text_evt_1": "wrapper"
        }
        index = build_index(loc)
        matches = find_event_text("evt", index)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].method, "exact_event")

    def test_deterministic_order(self):
        loc = {
            "vo_fmv_texts_text_evt": "e",
            "aide_de_camp_speeches_text_evt": "a",
            "pre_battle_speeches_text_evt": "d"
        }
        index = build_index(loc)
        matches = find_event_text("evt", index)
        keys = [m.ref.key for m in matches]
        self.assertEqual(keys, sorted(keys))

    def test_build_index_keeps_all_keys(self):
        index = build_index({'unrelated': 'a', 'UNRELATED': 'b'})
        self.assertEqual(index['unrelated'], (TextRef('unrelated', 'a'), TextRef('UNRELATED', 'b')))

    def test_only_one_play_prefix_is_removed(self):
        index = build_index({'aide_de_camp_speeches_text_evt': 'base'})
        self.assertEqual(find_event_text('Play_Play_evt', index), ())

if __name__ == "__main__":
    unittest.main()
