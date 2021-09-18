import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {SearchComponent} from "../search/search.component";
import {AnalyseComponent} from "../analyse/analyse.component";



const routes: Routes = [
  { path: '', redirectTo: '/search', pathMatch: 'full' },
  { path: 'search', component: SearchComponent },
  { path: 'analyse', component: AnalyseComponent }
];

@NgModule({
  imports: [ RouterModule.forRoot(routes) ],
  exports: [ RouterModule ]
})
export class AppRoutingModule {}
