import unittest

from src.jstris_keyboard_controller import (
    DEFAULT_KEY_BINDINGS,
    PlannedCommand,
    format_plan,
    load_key_bindings,
    plan_sequence,
)


class PlanSequenceTests(unittest.TestCase):
    def test_plans_basic_actions(self):
        planned = plan_sequence(["left", "rotate_cw", "hard_drop"])

        self.assertEqual(
            planned,
            [
                PlannedCommand(action="left", key="left"),
                PlannedCommand(action="rotate_cw", key="up"),
                PlannedCommand(action="hard_drop", key="space"),
            ],
        )

    def test_supports_aliases_commas_and_repeats(self):
        planned = plan_sequence(["l*2,cw", "drop"])

        self.assertEqual([command.action for command in planned], [
            "left",
            "left",
            "rotate_cw",
            "hard_drop",
        ])

    def test_supports_wait_tokens(self):
        planned = plan_sequence(["left", "wait:0.25*2", "right"])

        self.assertEqual(planned[0], PlannedCommand(action="left", key="left"))
        self.assertEqual(planned[1], PlannedCommand(action="wait", wait_seconds=0.25))
        self.assertEqual(planned[2], PlannedCommand(action="wait", wait_seconds=0.25))
        self.assertEqual(planned[3], PlannedCommand(action="right", key="right"))

    def test_custom_bindings_override_defaults(self):
        planned = plan_sequence(["hold"], {"hold": "shift"})

        self.assertEqual(planned, [PlannedCommand(action="hold", key="shift")])
        self.assertEqual(DEFAULT_KEY_BINDINGS["hold"], "c")

    def test_unknown_action_raises_helpful_error(self):
        with self.assertRaisesRegex(ValueError, "Unknown action `spin`"):
            plan_sequence(["spin"])

    def test_invalid_repeat_count_raises(self):
        with self.assertRaisesRegex(ValueError, "Repeat count must be at least 1"):
            plan_sequence(["left*0"])

    def test_empty_sequence_raises(self):
        with self.assertRaisesRegex(ValueError, "No actions"):
            plan_sequence([])

    def test_format_plan_is_human_readable(self):
        planned = plan_sequence(["left", "sleep:0.1", "hd"])

        self.assertEqual(format_plan(planned), "left(left) -> wait:0.1 -> hard_drop(space)")


class LoadKeyBindingsTests(unittest.TestCase):
    def test_load_key_bindings_requires_json_object(self):
        class FakePath:
            def open(self, *args, **kwargs):
                from io import StringIO

                return StringIO('["left"]')

        with self.assertRaisesRegex(ValueError, "JSON object"):
            load_key_bindings(FakePath())


if __name__ == "__main__":
    unittest.main()
