import unittest
from bank_graph import AudioNode, Resolution, resolve_event

class TestResolveEvent(unittest.TestCase):
    def test_single_chain(self):
        nodes = {
            1: AudioNode(1, 'CAkEvent', 'b', targets=(2,)),
            2: AudioNode(2, 'CAkActionPlay', 'b', targets=(3,)),
            3: AudioNode(3, 'CAkSound', 'b', media_id=100)
        }
        res = resolve_event(1, nodes)
        self.assertEqual(res.media_ids, (100,))
        self.assertEqual(res.missing_node_ids, ())
        self.assertEqual(res.unsupported_kinds, ())
        self.assertEqual(res.cycle_ids, ())

    def test_multi_action(self):
        nodes = {
            1: AudioNode(1, 'CAkEvent', 'b', targets=(2, 3)),
            2: AudioNode(2, 'CAkActionPlay', 'b', targets=(4,)),
            3: AudioNode(3, 'CAkActionPlay', 'b', targets=(5,)),
            4: AudioNode(4, 'CAkSound', 'b', media_id=100),
            5: AudioNode(5, 'CAkSound', 'b', media_id=200)
        }
        res = resolve_event(1, nodes)
        self.assertEqual(res.media_ids, (100, 200))
        self.assertEqual(res.missing_node_ids, ())
        self.assertEqual(res.unsupported_kinds, ())
        self.assertEqual(res.cycle_ids, ())

    def test_shared_leaf_dag_no_cycle(self):
        nodes = {
            1: AudioNode(1, 'CAkEvent', 'b', targets=(2, 3)),
            2: AudioNode(2, 'CAkRanSeqCntr', 'b', targets=(4,)),
            3: AudioNode(3, 'CAkActorMixer', 'b', targets=(4,)),
            4: AudioNode(4, 'CAkSound', 'b', media_id=100)
        }
        res = resolve_event(1, nodes)
        self.assertEqual(res.media_ids, (100,))
        self.assertEqual(res.cycle_ids, ())

    def test_directed_cycle(self):
        nodes = {
            1: AudioNode(1, 'CAkEvent', 'b', targets=(2,)),
            2: AudioNode(2, 'CAkActionPlay', 'b', targets=(3,)),
            3: AudioNode(3, 'CAkActionPlay', 'b', targets=(2,))
        }
        res = resolve_event(1, nodes)
        self.assertEqual(res.cycle_ids, (2, 3))
        self.assertEqual(res.media_ids, ())

    def test_missing_node(self):
        nodes = {
            1: AudioNode(1, 'CAkEvent', 'b', targets=(2,)),
            2: AudioNode(2, 'CAkActionPlay', 'b', targets=(99,))
        }
        res = resolve_event(1, nodes)
        self.assertEqual(res.missing_node_ids, (99,))
        self.assertEqual(res.media_ids, ())

    def test_unsupported_kind(self):
        nodes = {
            1: AudioNode(1, 'CAkEvent', 'b', targets=(2,)),
            2: AudioNode(2, 'CAkAttenuation', 'b', targets=(3,)),
            3: AudioNode(3, 'CAkSound', 'b', media_id=100)
        }
        res = resolve_event(1, nodes)
        self.assertEqual(res.unsupported_kinds, ('CAkAttenuation',))
        self.assertEqual(res.media_ids, ())

    def test_partial_success(self):
        nodes = {
            1: AudioNode(1, 'CAkEvent', 'b', targets=(2, 3)),
            2: AudioNode(2, 'CAkActionPlay', 'b', targets=(4,)),
            3: AudioNode(3, 'CAkUnknown', 'b', targets=(5,)),
            4: AudioNode(4, 'CAkSound', 'b', media_id=100),
            5: AudioNode(5, 'CAkSound', 'b', media_id=200)
        }
        res = resolve_event(1, nodes)
        self.assertEqual(res.media_ids, (100,))
        self.assertEqual(res.unsupported_kinds, ('CAkUnknown',))

    def test_stop_action_does_not_add_media_or_an_unsupported_branch(self):
        nodes = {
            1: AudioNode(1, 'CAkEvent', 'b', targets=(2, 3)),
            2: AudioNode(2, 'CAkActionStop', 'b', targets=(999,)),
            3: AudioNode(3, 'CAkSound', 'b', media_id=100)
        }
        self.assertEqual(resolve_event(1, nodes), Resolution((100,), (), (), ()))

if __name__ == '__main__':
    unittest.main()
