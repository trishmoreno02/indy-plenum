import json
from collections import OrderedDict
from functools import partial
from logging import getLogger
from typing import Any, Iterable

from plenum.common.event_bus import ExternalBus
from plenum.common.messages.node_message_factory import node_message_factory
from plenum.common.timer import TimerService
from plenum.server.replica_helper import getNodeName
from plenum.test.simulation.sim_random import SimRandom


class SimNetwork:
    def __init__(self, timer: TimerService, random: SimRandom):
        self._timer = timer
        self._random = random
        self._min_latency = 1
        self._max_latency = 500
        self._filters = {}
        self._logger = getLogger()
        self._peers = OrderedDict()  # type: OrderedDict[str, ExternalBus]

    def create_peer(self, name: str, handler=None) -> ExternalBus:
        if name in self._peers:
            raise ValueError("Peer with name '{}' already exists".format(name))

        handler = handler or partial(self._send_message, name)
        bus = ExternalBus(handler)
        self._peers[name] = bus
        return bus

    def set_latency(self, min_value: int, max_value: int):
        self._min_latency = min_value
        self._max_latency = max_value

    def reset_filters(self, names: Iterable=None, messages_types: Iterable=None):
        if names is None:
            names = self._peers.keys()
        for name in names:
            if name not in self._filters:
                continue
            if messages_types is None:
                self._filters[name].clear()
                continue
            for msg_type in messages_types:
                self._filters[name].pop(msg_type, None)

    def set_filter(self, names: Iterable, messages_types: Iterable):
        if messages_types:
            for name in names:
                self._filters.setdefault(name, set())
                self._filters[name].update(messages_types)

    def _send_message(self, frm: str, msg: Any, dst: ExternalBus.Destination):
        if dst is None:
            dst = [name for name in self._peers if name != getNodeName(frm)]
        elif isinstance(dst, str):
            dst = [dst]
        elif isinstance(dst, Iterable):
            assert len(dst) > 0, "{} tried to send message {} to no one".format(frm, msg)
        else:
            assert False, "{} tried to send message {} to unsupported destination {}".format(frm, msg, dst)

        for name in sorted(dst):
            assert name != frm, "{} tried to send message {} to itself".format(frm, msg)

            peer = self._peers.get(name)
            assert peer, "{} tried to send message {} to unknown peer {}".format(frm, msg, name)

            if name in self._filters and type(msg) in self._filters[name]:
                self._logger.debug("Discard {} for {} because it filtered by SimNetwork".format(msg, name))
                return

            self._timer.schedule(self._random.integer(self._min_latency, self._max_latency),
                                 partial(peer.process_incoming, msg, frm))
