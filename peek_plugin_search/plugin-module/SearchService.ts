import {Injectable} from "@angular/core";


import {
    ComponentLifecycleEventEmitter,
    extend,
    Payload,
    PayloadEnvelope,
    TupleOfflineStorageNameService,
    TupleOfflineStorageService,
    TupleSelector,
    TupleStorageFactoryService,
    VortexService,
    VortexStatusService
} from "@synerty/vortexjs";


import {Subject} from "rxjs/Subject";
import {Observable} from "rxjs/Observable";
import {PrivateSearchIndexLoaderService} from "./_private/search-index-loader";
import {PrivateSearchObjectLoaderService} from "./_private/search-object-loader";

import {SearchResultObjectTuple} from "./SearchResultObjectTuple";
import {SearchObjectTypeTuple} from "./SearchObjectTypeTuple";
import {OfflineConfigTuple, SearchPropertyTuple, SearchTupleService} from "./_private";
import {keywordSplitter} from "./_private/KeywordSplitter";


export interface SearchPropT {
    title: string;
    value: string;
    order: number;
}


// ----------------------------------------------------------------------------
/** LocationIndex Cache
 *
 * This class has the following responsibilities:
 *
 * 1) Maintain a local storage of the index
 *
 * 2) Return DispKey locations based on the index.
 *
 */
@Injectable()
export class SearchService extends ComponentLifecycleEventEmitter {
    // From python string.punctuation

    private offlineConfig: OfflineConfigTuple = new OfflineConfigTuple();

    // Passed to each of the results
    private propertiesByName: { [key: string]: SearchPropertyTuple; } = {};

    // Passed to each of the results
    private objectTypesById: { [key: number]: SearchObjectTypeTuple; } = {};

    constructor(private vortexStatusService: VortexStatusService,
                private tupleService: SearchTupleService,
                private searchIndexLoader: PrivateSearchIndexLoaderService,
                private searchObjectLoader: PrivateSearchObjectLoaderService) {
        super();


        this.tupleService.offlineObserver
            .subscribeToTupleSelector(new TupleSelector(OfflineConfigTuple.tupleName, {}))
            .takeUntil(this.onDestroyEvent)
            .filter(v => v.length != 0)
            .subscribe((tuples: OfflineConfigTuple[]) => {
                this.offlineConfig = tuples[0];
            });

        this._loadPropsAndObjs();

    }

    private _loadPropsAndObjs(): void {

        let propTs = new TupleSelector(SearchPropertyTuple.tupleName, {});
        this.tupleService.offlineObserver
            .subscribeToTupleSelector(propTs)
            .takeUntil(this.onDestroyEvent)
            .subscribe((tuples: SearchPropertyTuple[]) => {
                this.propertiesByName = {};

                for (let item of tuples) {
                    this.propertiesByName[item.name] = item;
                }
            });

        let objectTypeTs = new TupleSelector(SearchObjectTypeTuple.tupleName, {});
        this.tupleService.offlineObserver
            .subscribeToTupleSelector(objectTypeTs)
            .takeUntil(this.onDestroyEvent)
            .subscribe((tuples: SearchObjectTypeTuple[]) => {
                this.objectTypesById = {};

                for (let item of tuples) {
                    this.objectTypesById[item.id] = item;
                }
            });
    }


    /** Split Keywords
     *
     * @param {string} keywordStr: The keywords as one string
     * @returns {string[]} The keywords as an array
     */
    private splitKeywords(keywordStr: string): string[] {
        return keywordSplitter(keywordStr);
    }


    /** Get Locations
     *
     * Get the objects with matching keywords from the index..
     *
     */
    getObjects(propertyName: string | null,
               objectTypeId: number | null,
               keywordsString: string): Promise<SearchResultObjectTuple[]> {

        let keywords = this.splitKeywords(keywordsString);
        console.log(keywords);

        // If there is no offline support, or we're online
        if (!this.offlineConfig.cacheChunksForOffline
            || this.vortexStatusService.isOnline) {
            let ts = new TupleSelector(SearchResultObjectTuple.tupleName, {
                "propertyName": propertyName,
                "objectTypeId": objectTypeId,
                "keywords": keywords
            });

            let isOnlinePromise: any = this.vortexStatusService.snapshot.isOnline ?
                Promise.resolve() :
                this.vortexStatusService.isOnline
                    .filter(online => online)
                    .first()
                    .toPromise();

            return isOnlinePromise
                .then(() => this.tupleService.offlineObserver.pollForTuples(ts, false))
                .then(v => this._loadObjectTypes(v));
        }

        // If we do have offline support
        return this.searchIndexLoader.getObjectIds(propertyName, keywords)
            .then((objectIds: number[]) => {
                if (objectIds.length == 0) {
                    console.log("There were no keyword search results for : " + keywords);
                    return [];
                }

                // Limit to 20 results
                objectIds = objectIds.slice(0, 20);

                return this.searchObjectLoader.getObjects(objectTypeId, objectIds)
                    .then(v => this._loadObjectTypes(v));
            })

    }

    /** Get Nice Ordered Properties
     *
     * @param {SearchResultObjectTuple} obj
     * @returns {SearchPropT[]}
     */
    getNiceOrderedProperties(obj: SearchResultObjectTuple): SearchPropT[] {
        let props: SearchPropT[] = [];

        for (let name of Object.keys(obj.properties)) {
            let prop = this.propertiesByName[name.toLowerCase()] || new SearchPropertyTuple();
            props.push({
                title: prop.title,
                order: prop.order,
                value: obj.properties[name]
            });
        }
        props.sort((a, b) => a.order - b.order);

        return props;
    }

    /** Load Object Types
     *
     * Relinks the object types for search results.
     *
     * @param {SearchResultObjectTuple} searchObjects
     * @returns {SearchResultObjectTuple[]}
     */
    private _loadObjectTypes(searchObjects: SearchResultObjectTuple []): SearchResultObjectTuple[] {
        for (let searchObject of searchObjects) {
            searchObject.objectType = this.objectTypesById[searchObject.objectType.id];
        }
        return searchObjects;
    }

}