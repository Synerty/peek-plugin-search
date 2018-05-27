import logging
from datetime import datetime
from typing import List, Callable

import pytz
from sqlalchemy import asc
from twisted.internet import task
from twisted.internet.defer import inlineCallbacks

from peek_plugin_search._private.server.client_handlers.ClientSearchIndexChunkUpdateHandler import \
    ClientSearchIndexChunkUpdateHandler
from peek_plugin_search._private.server.controller.StatusController import \
    StatusController
from peek_plugin_search._private.storage.SearchIndexCompilerQueue import \
    SearchIndexCompilerQueue
from vortex.DeferUtil import deferToThreadWrapWithLogger, vortexLogFailure

logger = logging.getLogger(__name__)


class SearchChunkCompilerQueueController:
    """ SearchChunkCompilerQueueController

    Compile the disp items into the grid data

    1) Query for queue
    2) Process queue
    3) Delete from queue

    """

    FETCH_SIZE = 10
    PERIOD = 0.200

    QUEUE_MAX = 10
    QUEUE_MIN = 0

    def __init__(self, ormSessionCreator,
                 statusController: StatusController,
                 clientLocationUpdateHandler: ClientSearchIndexChunkUpdateHandler,
                 readyLambdaFunc: Callable):
        self._ormSessionCreator = ormSessionCreator
        self._statusController: StatusController = statusController
        self._clientLocationUpdateHandler: ClientSearchIndexChunkUpdateHandler = clientLocationUpdateHandler
        self._readyLambdaFunc = readyLambdaFunc

        self._pollLoopingCall = task.LoopingCall(self._poll)
        self._lastQueueId = -1
        self._queueCount = 0

    def start(self):
        self._statusController.setLocationIndexCompilerStatus(True, self._queueCount)
        d = self._pollLoopingCall.start(self.PERIOD, now=False)
        d.addCallbacks(self._timerCallback, self._timerErrback)

    def _timerErrback(self, failure):
        vortexLogFailure(failure, logger)
        self._statusController.setLocationIndexCompilerStatus(False, self._queueCount)
        self._statusController.setLocationIndexCompilerError(str(failure.value))

    def _timerCallback(self, _):
        self._statusController.setLocationIndexCompilerStatus(False, self._queueCount)

    def stop(self):
        self._pollLoopingCall.stop()

    def shutdown(self):
        self.stop()

    @inlineCallbacks
    def _poll(self):
        if not self._readyLambdaFunc():
            return

        from peek_plugin_search._private.worker.tasks.SearchChunkCompilerTask import \
            compileSearchChunk

        # We queue the grids in bursts, reducing the work we have to do.
        if self._queueCount > self.QUEUE_MIN:
            return

        # Check for queued items
        queueItems = yield self._grabQueueChunk()
        if not queueItems:
            return

        # De duplicated queued grid keys
        # This is the reason why we don't just queue all the celery tasks in one go.
        # If we keep them in the DB queue, we can remove the duplicates
        # and there are lots of them
        queueIdsToDelete = []

        locationIndexBucketSet = set()
        for i in queueItems:
            if i.indexBucket in locationIndexBucketSet:
                queueIdsToDelete.append(i.id)
            else:
                locationIndexBucketSet.add(i.indexBucket)

        if queueIdsToDelete:
            # Delete the duplicates and requery for our new list
            yield self._deleteDuplicateQueueItems(queueIdsToDelete)
            queueItems = yield self._grabQueueChunk()

        # Send the tasks to the peek worker
        for start in range(0, len(queueItems), self.FETCH_SIZE):

            items = queueItems[start: start + self.FETCH_SIZE]

            # Set the watermark
            self._lastQueueId = items[-1].id

            d = compileSearchChunk.delay(items)
            d.addCallback(self._pollCallback, datetime.now(pytz.utc), len(items))
            d.addErrback(self._pollErrback, datetime.now(pytz.utc))

            self._queueCount += 1
            if self._queueCount >= self.QUEUE_MAX:
                break

    @deferToThreadWrapWithLogger(logger)
    def _grabQueueChunk(self):
        session = self._ormSessionCreator()
        try:
            qry = (session.query(SearchIndexCompilerQueue)
                .order_by(asc(SearchIndexCompilerQueue.id))
                .filter(SearchIndexCompilerQueue.id > self._lastQueueId)
                .yield_per(500)
                # .limit(self.FETCH_SIZE)
                )

            queueItems = qry.all()
            session.expunge_all()

            return queueItems

        finally:
            session.close()

    @deferToThreadWrapWithLogger(logger)
    def _deleteDuplicateQueueItems(self, itemIds):
        session = self._ormSessionCreator()
        table = SearchIndexCompilerQueue.__table__
        try:
            SIZE = 1000
            for start in range(0, len(itemIds), SIZE):
                chunkIds = itemIds[start: start + SIZE]

                session.execute(table.delete(table.c.id.in_(chunkIds)))

            session.commit()
        finally:
            session.close()

    def _pollCallback(self, indexBuckets: List[str], startTime, processedCount):
        self._queueCount -= 1
        logger.debug("Time Taken = %s" % (datetime.now(pytz.utc) - startTime))
        self._clientLocationUpdateHandler.sendChunks(indexBuckets)
        self._statusController.addToLocationIndexCompilerTotal(processedCount)
        self._statusController.setLocationIndexCompilerStatus(True, self._queueCount)

    def _pollErrback(self, failure, startTime):
        self._queueCount -= 1
        self._statusController.setLocationIndexCompilerError(str(failure.value))
        self._statusController.setLocationIndexCompilerStatus(True, self._queueCount)
        logger.debug("Time Taken = %s" % (datetime.now(pytz.utc) - startTime))
        vortexLogFailure(failure, logger)