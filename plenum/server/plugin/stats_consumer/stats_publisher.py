import asyncio

from enum import Enum, unique

from plenum.common.log import getlogger

logger = getlogger()


class StatsPublisher:
    """
    Class to send data to TCP port which runs stats collecting service
    """

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None

    async def sendMessage(self, message):
        loop = asyncio.get_event_loop()
        try:
            if self.writer is None:
                self.reader, self.writer = await asyncio.streams\
                    .open_connection(self.ip, self.port, loop=loop)
            self.writer.write((message + '\n').encode('utf-8'))
            await self.writer.drain()
        except (ConnectionRefusedError, ConnectionResetError) as ex:
            logger.debug("connection refused for {}:{} while sending message".
                         format(self.ip, self.port))
            self.writer = None

    def send(self, message):
        async def run():
            await self.sendMessage(message=message)
            # TODO: Can this sleep be removed?
            await asyncio.sleep(0.01)

        loop = asyncio.get_event_loop()

        if loop.is_running():
            loop.call_soon(asyncio.async, run())
        else:
            loop.run_until_complete(run())


@unique
class Topic(Enum):
    ComputeLatencies = 1
    ComputeMasterThroughput = 2
    ComputeTotalTransactions = 3
    PublishMtrStats = 4
    PublishLatenciesStats = 5
    PublishConfig = 6
    PublishStartedAt = 7
    PublishViewChange = 8
    PublishTotalTransactions = 9
    PublishAllStats = 10
    IncomingEvent = 11,
    PublishNodestackStats = 12
    PublishTotalRequestsStats = 13

    def __str__(self):
        return self.name
