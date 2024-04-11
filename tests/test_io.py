import unittest
from queue import Queue
from flyde.io import Input, InputMode, EOF

class TestInput(unittest.TestCase):
    def setUp(self):
        self.input = Input()

    def test_init(self):
        test_cases = [
            {'name': 'default input', 'expected': (InputMode.QUEUE, None, None)},
            {'name': 'input with type', 'type': int, 'expected': (InputMode.QUEUE, int, None)},
            {'name': 'input with value', 'value': 10, 'expected': (InputMode.QUEUE, None, 10)},
            {'name': 'input with type and invalid value', 'type': int, 'value': 'string', 'expected': (InputMode.QUEUE, int, None), 'raises': ValueError},
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case['name']):
                args = {}
                if 'mode' in test_case:
                    args['mode'] = test_case['mode']
                if 'type' in test_case:
                    args['type'] = test_case['type']
                if 'value' in test_case:
                    args['value'] = test_case['value']
                if 'raises' in test_case:
                    with self.assertRaises(test_case['raises']):
                        self.input = Input(**args)
                else:
                    self.input = Input(**args)
                    self.assertEqual((self.input.mode, self.input.type, self.input.value), test_case['expected'])

    def test_connect(self):
        queue = Queue()
        self.input.connect(queue)
        self.assertEqual(self.input.queue, queue)

    def test_set_value(self):
        test_cases = [
            {'name': 'valid integer', 'type': int, 'value': 10, 'expected': 10, 'raises': None},
            {'name': 'invalid string', 'type': int, 'value': 'string', 'expected': None, 'raises': ValueError},
            {'name': 'EOF as a valid case', 'type': int, 'value': EOF, 'expected': EOF, 'raises': None},
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case['name']):
                self.input = Input(type=test_case['type'])
                if test_case['raises']:
                    with self.assertRaises(test_case['raises']):
                        self.input.set_value(test_case['value'])
                else:
                    self.input.set_value(test_case['value'])
                    self.assertEqual(self.input.value, test_case['expected'])

    def test_get(self):
        test_cases = [
            {'name': 'get valid value in queue mode', 'mode': InputMode.QUEUE, 'queue_values': [10], 'expected': 10, 'raises': None},
            {'name': 'get EOF in queue mode', 'mode': InputMode.QUEUE, 'queue_values': [EOF], 'expected': None, 'raises': Exception},
            {'name': 'get value in static mode', 'mode': InputMode.STATIC, 'value': 10, 'expected': 10, 'raises': None},
            {'name': 'get value in sticky mode', 'mode': InputMode.STICKY, 'value': 10, 'expected': 10, 'raises': None},
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case['name']):
                self.input = Input(mode=test_case['mode'])
                if 'queue_values' in test_case:
                    queue = Queue()
                    self.input.connect(queue)
                    for value in test_case['queue_values']:
                        queue.put(value)
                if 'value' in test_case:
                    self.input.set_value(test_case['value'])
                if test_case['raises']:
                    with self.assertRaises(test_case['raises']):
                        self.input.get()
                else:
                    self.assertEqual(self.input.get(), test_case['expected'])

    def test_empty(self):
        test_cases = [
            {'name': 'empty input in queue mode', 'mode': InputMode.QUEUE, 'queue_values': [], 'expected': True},
            {'name': 'non-empty input in queue mode', 'mode': InputMode.QUEUE, 'queue_values': [10], 'expected': False},
            {'name': 'empty input in static mode', 'mode': InputMode.STATIC, 'value': None, 'expected': True},
            {'name': 'non-empty input in static mode', 'mode': InputMode.STATIC, 'value': 10, 'expected': False},
            {'name': 'empty input in sticky mode', 'mode': InputMode.STICKY, 'value': None, 'expected': True},
            {'name': 'non-empty input in sticky mode', 'mode': InputMode.STICKY, 'value': 10, 'expected': False},
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case['name']):
                self.input = Input(mode=test_case['mode'])
                if 'queue_values' in test_case:
                    queue = Queue()
                    self.input.connect(queue)
                    for value in test_case['queue_values']:
                        queue.put(value)
                if 'value' in test_case:
                    self.input.set_value(test_case['value'])
                self.assertEqual(self.input.empty(), test_case['expected'])

    def test_count(self):
        test_cases = [
            {'name': 'count with one item in queue mode', 'mode': InputMode.QUEUE, 'queue_values': [10], 'expected': 1},
            {'name': 'count with no item in queue mode', 'mode': InputMode.QUEUE, 'queue_values': [], 'expected': 0},
            {'name': 'count in static mode', 'mode': InputMode.STATIC, 'value': 10, 'expected': 1},
            {'name': 'count in sticky mode', 'mode': InputMode.STICKY, 'value': 10, 'expected': 1},
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case['name']):
                self.input = Input(mode=test_case['mode'])
                if 'queue_values' in test_case:
                    queue = Queue()
                    self.input.connect(queue)
                    for value in test_case['queue_values']:
                        queue.put(value)
                if 'value' in test_case:
                    self.input.set_value(test_case['value'])
                self.assertEqual(self.input.count(), test_case['expected'])

if __name__ == '__main__':
    unittest.main()
