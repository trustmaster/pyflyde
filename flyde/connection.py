class ConnectionNode:
    ins_id: str
    pin_id: str

    def __init__(self, ins_id: str, pin_id: str):
        self.ins_id = ins_id
        self.pin_id = pin_id


class Connection:
    """Connection is a connection between two nodes."""

    def __init__(self, from_node: ConnectionNode, to_node: ConnectionNode, delayed: bool = False, hidden: bool = False):
        self.from_node = from_node
        self.to_node = to_node
        self.delayed = delayed
        self.hidden = hidden

    def set_queue(self, queue):
        self.queue = queue

    @classmethod
    def from_yaml(cls, yml: dict):
        return cls(
            ConnectionNode(yml['from']['insId'], yml['from']['pinId']),
            ConnectionNode(yml['to']['insId'], yml['to']['pinId']),
            yml.get('delayed', False),
            yml.get('hidden', False)
        )

    def to_dict(self) -> dict:
        return {
            'from': {
                'insId': self.from_node.ins_id,
                'pinId': self.from_node.pin_id
            },
            'to': {
                'insId': self.to_node.ins_id,
                'pinId': self.to_node.pin_id
            },
            'delayed': self.delayed,
            'hidden': self.hidden
        }
