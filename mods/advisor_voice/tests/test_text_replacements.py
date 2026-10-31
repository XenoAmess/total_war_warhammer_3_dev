import unittest
from text_replacements import resolve_replacements, ReplacementResult

class TestTextReplacements(unittest.TestCase):
    def test_nested_chinese(self):
        loc = {
            "ui_text_replacements_localised_text_outer": "Hello {{tr:inner}}",
            "ui_text_replacements_localised_text_inner": "你好"
        }
        res = resolve_replacements("{{tr:outer}}", loc)
        self.assertEqual(res.text, "Hello 你好")
        self.assertEqual(res.source_keys, ("ui_text_replacements_localised_text_inner", "ui_text_replacements_localised_text_outer"))
        self.assertEqual(res.unresolved, ())

    def test_separate_repeated_branches(self):
        loc = {
            "ui_text_replacements_localised_text_a": "{{tr:b}} {{tr:b}}",
            "ui_text_replacements_localised_text_b": "x"
        }
        res = resolve_replacements("{{tr:a}}", loc)
        self.assertEqual(res.text, "x x")
        self.assertEqual(res.source_keys, ("ui_text_replacements_localised_text_a", "ui_text_replacements_localised_text_b"))
        self.assertEqual(res.unresolved, ())

    def test_unknown_preservation(self):
        loc = {"ui_text_replacements_localised_text_known": "ok"}
        res = resolve_replacements("{{tr:unknown}}", loc)
        self.assertEqual(res.text, "{{tr:unknown}}")
        self.assertEqual(res.source_keys, ())
        self.assertEqual(res.unresolved, ("unknown",))

    def test_cycle_preservation(self):
        loc = {
            "ui_text_replacements_localised_text_a": "{{tr:b}}",
            "ui_text_replacements_localised_text_b": "{{tr:a}}"
        }
        res = resolve_replacements("{{tr:a}}", loc)
        self.assertEqual(res.text, "{{tr:a}}")
        self.assertEqual(res.source_keys, ("ui_text_replacements_localised_text_a", "ui_text_replacements_localised_text_b"))
        self.assertEqual(res.unresolved, ("a",))

    def test_empty_values(self):
        loc = {"ui_text_replacements_localised_text_empty": ""}
        res = resolve_replacements("{{tr:empty}}", loc)
        self.assertEqual(res.text, "")
        self.assertEqual(res.source_keys, ("ui_text_replacements_localised_text_empty",))
        self.assertEqual(res.unresolved, ())

    def test_unrelated_markup(self):
        loc = {"ui_text_replacements_localised_text_x": "<b>{{tr:y}}</b>"}
        res = resolve_replacements("{{tr:x}}", loc)
        self.assertEqual(res.text, "<b>{{tr:y}}</b>")
        self.assertEqual(res.source_keys, ("ui_text_replacements_localised_text_x",))
        self.assertEqual(res.unresolved, ("y",))

    def test_game_advice_loc(self):
        loc = {
            "ui_text_replacements_localised_text_skaven_endgame_foreshadow_speech": "你好"
        }
        res = resolve_replacements("{{tr:skaven_endgame_foreshadow_speech}}", loc)
        self.assertEqual(res.text, "你好")
        self.assertEqual(res.source_keys, ("ui_text_replacements_localised_text_skaven_endgame_foreshadow_speech",))
        self.assertEqual(res.unresolved, ())

    def test_depth_limit_preserves_and_reports_marker(self):
        loc = {f'ui_text_replacements_localised_text_{i}': '{{tr:' + str(i + 1) + '}}'
               for i in range(20)}
        res = resolve_replacements('{{tr:0}}', loc)
        self.assertEqual(res.text, '{{tr:17}}')
        self.assertEqual(res.unresolved, ('17',))

    def test_alias_is_not_trimmed_or_case_folded(self):
        loc = {'ui_text_replacements_localised_text_ X ': '字幕'}
        res = resolve_replacements('{{tr: X }} {{tr:x}}', loc)
        self.assertEqual(res.text, '字幕 {{tr:x}}')
        self.assertEqual(res.unresolved, ('x',))

if __name__ == "__main__":
    unittest.main()
