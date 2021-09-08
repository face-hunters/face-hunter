import {Component, OnInit} from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {

  value: any;

  videos: any[] = [];

  constructor(){
    this.value = '';
    this.videos = []
  }

  ngOnInit() {
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.body.appendChild(tag);
  }

  get_videos_of_celebritiy() {
    this.videos.push({id: 'LKvlfxVC210', start: 3, end: 15, duration: 12});
    this.videos.push({id: 'N_gD9-Oa0fg', start: 3, end: 20, duration: 17});
  }

  reset() {
    this.videos = [];
  }

}
