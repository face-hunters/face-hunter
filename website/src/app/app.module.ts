import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import {MatToolbarModule} from '@angular/material/toolbar';
import {YouTubePlayerModule} from "@angular/youtube-player";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatIconModule} from "@angular/material/icon";
import {MatInputModule} from "@angular/material/input";
import {MatButtonModule} from "@angular/material/button";
import {MatDialogModule} from "@angular/material/dialog";
import {SparqlDialogComponent} from "../sparql-dialog/sparql-dialog.component";
import {MatDividerModule} from "@angular/material/divider";
import {AppRoutingModule} from "./app-routing.module";
import {SearchComponent} from "../search/search.component";
import {HttpClientModule} from "@angular/common/http";
import {HunterService} from "../services/hunter.service";
import {FormsModule} from "@angular/forms";
import {NotFoundDialogComponent} from "../not-found-dialog/not-found-dialog.component";
import {YamlService} from "../services/yaml.service";

@NgModule({
  declarations: [
    AppComponent,
    SparqlDialogComponent,
    NotFoundDialogComponent,
    SearchComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    MatToolbarModule,
    YouTubePlayerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatDividerModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule
  ],
  providers: [
    HunterService,
    YamlService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
