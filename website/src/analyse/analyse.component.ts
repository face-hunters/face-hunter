import {Component, OnInit} from '@angular/core';
import {MatDialog} from "@angular/material/dialog";
import {SparqlDialogComponent} from "../sparql-dialog/sparql-dialog.component";

@Component({
  selector: 'analyse',
  templateUrl: './analyse.component.html',
  styleUrls: ['./analyse.component.scss']
})
export class AnalyseComponent implements OnInit{

  value: any;

  videos: any[] = [];

  constructor(public dialog: MatDialog) {
    this.value = '';
    this.videos = []
  }

  ngOnInit() {
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.body.appendChild(tag);
  }

  get_videos_of_celebritiy() {
    this.videos.push({id: 'LKvlfxVC210', start: 3, end: 15, duration: 12, video: 'Test', entity: 'Adam Sandler'});
    this.videos.push({id: 'N_gD9-Oa0fg', start: 3, end: 20, duration: 17, video: 'Test', entity: 'Adam Sandler'});
    this.videos.push({id: 'N_gD9-Oa0fg', start: 3, end: 20, duration: 17, video: 'Test', entity: 'Adam Sandler'});
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
        this.get_videos_of_celebritiy()
      }
    });
  }

}