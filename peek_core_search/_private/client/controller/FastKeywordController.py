""" Fast Graph DB

This module stores a memory resident model of a graph network.

"""
import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional, List, Dict

import pytz
import ujson
from twisted.internet.defer import inlineCallbacks, Deferred
from vortex.DeferUtil import deferToThreadWrapWithLogger
from vortex.Payload import Payload
from vortex.TupleAction import TupleActionABC
from vortex.handler.TupleActionProcessor import TupleActionProcessorDelegateABC

from peek_core_search._private.client.controller.SearchIndexCacheController import \
    SearchIndexCacheController
from peek_core_search._private.client.controller.SearchObjectCacheController import \
    SearchObjectCacheController
from peek_core_search._private.storage.EncodedSearchIndexChunk import \
    EncodedSearchIndexChunk
from peek_core_search._private.tuples.KeywordAutoCompleteTupleAction import \
    KeywordAutoCompleteTupleAction
from peek_core_search._private.worker.tasks.ImportSearchIndexTask import _splitKeywords
from peek_core_search._private.worker.tasks._CalcChunkKey import makeSearchIndexChunkKey

logger = logging.getLogger(__name__)


class FastKeywordController(TupleActionProcessorDelegateABC):
    def __init__(self, objectCacheController: SearchObjectCacheController,
                 indexCacheController: SearchIndexCacheController):
        self._objectCacheController = objectCacheController
        self._indexCacheController = indexCacheController
        self._objectIdsByKeywordByPropertyKeyByChunkKey: Dict[
            str, Dict[str, Dict[str, List[int]]]] = {}

    def shutdown(self):
        self._objectCacheController = None
        self._indexCacheController = None
        self._objectIdsByKeywordByPropertyKeyByChunkKey = {}

    @inlineCallbacks
    def processTupleAction(self, tupleAction: TupleActionABC) -> Deferred:
        assert isinstance(tupleAction, KeywordAutoCompleteTupleAction), \
            "Tuple is not a KeywordAutoCompleteTupleAction"

        startTime = datetime.now(pytz.utc)

        objectIds = yield self.getObjectIdsForSearchString(
            tupleAction.searchString, tupleAction.propertyName
        )

        results = yield self._objectCacheController.getObjects(
            tupleAction.objectTypeId, objectIds
        )

        logger.debug("Completed search for |%s|, returning %s objects, in %s",
                     tupleAction.searchString,
                     len(results), (datetime.now(pytz.utc) - startTime))

        return results

    @deferToThreadWrapWithLogger(logger)
    def getObjectIdsForSearchString(self, searchString: str,
                                    propertyName: Optional[str]) -> Deferred:
        """ Get ObjectIds For Search String

        :rtype List[int]

        """
        splitKws = _splitKeywords(searchString)
        if not splitKws:
            return []

        # Create the structure to hold the IDs, for a match, we need an object id to be
        # in every row.
        results = {kw: [] for kw in splitKws}

        # Figure out which keywords are in which chunk keys
        keywordsByChunkKey = defaultdict(list)
        for kw in splitKws:
            keywordsByChunkKey[makeSearchIndexChunkKey(kw)].append(kw)

        # Iterate through each of the chunks we need
        for chunkKey, keywordsInThisChunk in keywordsByChunkKey.items():
            objectIdsByKeywordByPropertyKey = self \
                ._objectIdsByKeywordByPropertyKeyByChunkKey.get(chunkKey)

            if not objectIdsByKeywordByPropertyKey:
                logger.debug("No SearchIndex chunk exists with chunkKey |%s|", chunkKey)
                continue

            # Get the keywords for the property we're searching for
            objectIdsByKeywordListOfDicts = []
            if propertyName is None:
                # All property keys
                objectIdsByKeywordListOfDicts = objectIdsByKeywordByPropertyKey.values()

            elif propertyName in objectIdsByKeywordByPropertyKey:
                # A specific property key
                objectIdsByKeywordListOfDicts = [objectIdsByKeywordByPropertyKey[propertyName]]

            # Iterate through each of the property keys, this isn't a big list
            for objectIdsByKeyword in objectIdsByKeywordListOfDicts:
                for kw in keywordsInThisChunk:
                    if kw in objectIdsByKeyword:
                        results[kw] += objectIdsByKeyword[kw]

        objectIdsUnion = set(results.popitem()[1])
        while results:
            objectIdsUnion &= set(results.popitem()[1])

        return list(objectIdsUnion)[:50]

    @inlineCallbacks
    def notifyOfUpdate(self, chunkKeys: List[str]):
        """ Notify of Segment Updates

        This method is called by the client.SearchIndexCacheController when it receives
         updates from the server.

        """
        for chunkKey in chunkKeys:
            encodedChunkTuple = self._indexCacheController.encodedChunk(chunkKey)
            yield self._unpackKeywordsFromChunk(encodedChunkTuple)

    @deferToThreadWrapWithLogger(logger)
    def _unpackKeywordsFromChunk(self, chunk: EncodedSearchIndexChunk) -> None:

        chunkDataTuples = Payload().fromEncodedPayload(chunk.encodedData).tuples

        chunkData: Dict[str, Dict[str, List[int]]] = defaultdict(dict)

        for data in chunkDataTuples:
            keyword = data[EncodedSearchIndexChunk.ENCODED_DATA_KEYWORD_NUM]
            propertyName = data[EncodedSearchIndexChunk.ENCODED_DATA_PROPERTY_MAME_NUM]
            objectIdsJson = data[
                EncodedSearchIndexChunk.ENCODED_DATA_OBJECT_IDS_JSON_INDEX]
            chunkData[propertyName][keyword] = ujson.loads(objectIdsJson)

        self._objectIdsByKeywordByPropertyKeyByChunkKey[chunk.chunkKey] = chunkData
