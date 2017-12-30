import {CommonModule} from "@angular/common";
import {NgModule} from "@angular/core";
import {Routes} from "@angular/router";

// Import a small abstraction library to switch between nativescript and web
import {PeekModuleFactory} from "@synerty/peek-util/index.web";

// Import the default route component
import {UnifiedSearchComponent} from "./unifiedSearch.component";

// Import the required classes from VortexJS
import {
    TupleOfflineStorageNameService,
    TupleOfflineStorageService
} from "@synerty/vortexjs";

// Import the names we need for the
import {
    unifiedSearchTupleOfflineServiceName
} from "@peek/peek_plugin_unified_search/_private/PluginNames";

// Import the required classes from VortexJS
import {
    TupleDataObservableNameService,
    TupleDataObserverService,
    TupleDataOfflineObserverService
} from "@synerty/vortexjs";

// Import the names we need for the

import {ExcludedKwComponent} from "./search-component/search.component";

import {
    unifiedSearchObservableName,
    unifiedSearchFilt
} from "@peek/peek_plugin_unified_search/_private/PluginNames";

// Import the required classes from VortexJS
import {
    TupleActionPushNameService,
    TupleActionPushOfflineService,
    TupleActionPushService
} from "@synerty/vortexjs";

// Import the names we need for the
import {
    unifiedSearchActionProcessorName
} from "@peek/peek_plugin_unified_search/_private";


export function tupleActionPushNameServiceFactory() {
    return new TupleActionPushNameService(
        unifiedSearchActionProcessorName, unifiedSearchFilt);
}

export function tupleDataObservableNameServiceFactory() {
    return new TupleDataObservableNameService(
        unifiedSearchObservableName, unifiedSearchFilt);
}

export function tupleOfflineStorageNameServiceFactory() {
    return new TupleOfflineStorageNameService(unifiedSearchTupleOfflineServiceName);
}

// Define the child routes for this plugin
export const pluginRoutes: Routes = [
    {
        path: 'stringint',
        component: ExcludedKwComponent
    },
    {
        path: '',
        pathMatch: 'full',
        component: UnifiedSearchComponent
    }

];

// Define the root module for this plugin.
// This module is loaded by the lazy loader, what ever this defines is what is started.
// When it first loads, it will look up the routs and then select the component to load.
@NgModule({
    imports: [
        CommonModule,
        PeekModuleFactory.RouterModule,
        PeekModuleFactory.RouterModule.forChild(pluginRoutes),
        ...PeekModuleFactory.FormsModules,
    ],
    exports: [],
    providers: [
        TupleActionPushOfflineService, TupleActionPushService, {
            provide: TupleActionPushNameService,
            useFactory: tupleActionPushNameServiceFactory
        },
        TupleOfflineStorageService, {
            provide: TupleOfflineStorageNameService,
            useFactory: tupleOfflineStorageNameServiceFactory
        },
        TupleDataObserverService, TupleDataOfflineObserverService, {
            provide: TupleDataObservableNameService,
            useFactory: tupleDataObservableNameServiceFactory
        },
    ],
    declarations: [UnifiedSearchComponent, ExcludedKwComponent]
})
export class UnifiedSearchModule {
}
