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
        this.videos.push({id: 'LKvlfxVC210', start: 3, end: 15, duration: 12, video: 'Test', entity: 'Adam Sandler'});
        this.videos.push({id: 'N_gD9-Oa0fg', start: 3, end: 20, duration: 17, video: 'Test', entity: 'Adam Sandler'});
        this.videos.push({id: 'N_gD9-Oa0fg', start: 3, end: 20, duration: 17, video: 'Test', entity: 'Adam Sandler'});
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
        this.get_videos_of_celebritiy('Adam Sandler')
      }
    });
  }

}
