import {Component, Inject, OnInit} from '@angular/core';
import {MatDialog} from "@angular/material/dialog";
import {SparqlDialogComponent} from "../sparql-dialog/sparql-dialog.component";
import {HunterService} from "../services/hunter.service";
import {NotFoundDialogComponent} from "../not-found-dialog/not-found-dialog.component";
import {DOCUMENT} from "@angular/common";

@Component({
  selector: 'search',
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.scss']
})
export class SearchComponent implements OnInit {

  entity: string = '';

  value: any;

  allVideos: any;
  videos: any[] = [];

  currentPage = 0;

  constructor(public dialog: MatDialog,
              private hunter: HunterService,
              @Inject(DOCUMENT) public document: Document) {
    this.value = '';
    this.allVideos = [];
    this.videos = [];
  }

  ngOnInit() {
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.body.appendChild(tag);
  }

  process_scene(raw_data: any) {
    for (let scene in raw_data) {
      let start_split = raw_data[scene][3].split(':');
      let end_split = raw_data[scene][4].split(':');
      let start = +start_split[0]*24*60 + +start_split[1]*60 + +start_split[2];
      let end = +end_split[0]*24*60 + +end_split[1]*60 + +end_split[2];

      this.allVideos.push({video: raw_data[scene][0],
        id: raw_data[scene][1].split('=')[raw_data[scene][1].split('=').length - 1],
        start: start,
        end: end,
        duration: end - start,
        entity: raw_data[scene][2]})
    }
    console.log(this.allVideos)
  }

  get_videos_of_celebritiy(name: string) {
    console.log(name);
    this.hunter.get_scenes_of_entity(name).subscribe(data => {
      if (data['result'] == null) {
        this.dialog.open(NotFoundDialogComponent);
      } else {
        this.process_scene(data.result);
        this.videos = this.allVideos.slice(0, 5);
      }
    });
  }

  reset() {
    this.allVideos = [];
    this.videos = [];
  }

  openDialog(): void {
    const dialogRef = this.dialog.open(SparqlDialogComponent, {
      width: '500px',
      data: {}
    });

    dialogRef.afterClosed().subscribe(query_data => {
      if (query_data != null) {
        console.log(query_data);
        this.hunter.execute_query(query_data).subscribe(data => {
          console.log(data);
          this.process_scene(data.result)
          this.videos = this.allVideos.slice(0, 5);
        })
      }
    });
  }

  backward():void {
    this.currentPage -= 5;
    this.videos = this.allVideos.slice(this.currentPage, this.currentPage + 5);
  }

  forward():void {
    this.currentPage += 5;
    this.videos = this.allVideos.slice(this.currentPage, this.currentPage + 5);
    console.log(this.currentPage)
  }

}
