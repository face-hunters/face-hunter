import {Component, OnInit} from '@angular/core';
import {MatDialog} from "@angular/material/dialog";
import {SparqlDialogComponent} from "../sparql-dialog/sparql-dialog.component";
import {HunterService} from "../services/hunter.service";
import {NotFoundDialogComponent} from "../not-found-dialog/not-found-dialog.component";

@Component({
  selector: 'search',
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.scss']
})
export class SearchComponent implements OnInit {

  entity: string = '';

  value: any;

  videos: any[] = [];

  constructor(public dialog: MatDialog,
              private hunter: HunterService) {
    this.value = '';
    this.videos = [];
  }

  ngOnInit() {
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.body.appendChild(tag);
  }

  get_videos_of_celebritiy(name: string) {
    console.log(name);
    this.hunter.get_scenes_of_entity(name).subscribe(data => {
      if (data['result'] == null) {
        this.dialog.open(NotFoundDialogComponent);
      } else {
        for (let scene in data.result) {
          let start_split = data.result[scene][2].split(':');
          let end_split = data.result[scene][3].split(':');
          let start = +start_split[0]*24*60 + +start_split[1]*60 + +start_split[2];
          let end = +end_split[0]*24*60 + +end_split[1]*60 + +end_split[2];

          this.videos.push({video: data.result[0][0],
            id: data.result[scene][1].split('=')[data.result[scene][1].split('=').length - 1],
            start: start,
            end: end,
            duration: end - start,
            entity: name})
        }
        console.log(this.videos)
      }
    });
  }

  reset() {
    this.videos = [];
  }

  openDialog(): void {
    const dialogRef = this.dialog.open(SparqlDialogComponent, {
      width: '500px',
      data: {}
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result != null) {
        console.log(result);
        this.hunter.execute_query(result).subscribe(data => {
          console.log(data);
        })
      }
    });
  }

}
