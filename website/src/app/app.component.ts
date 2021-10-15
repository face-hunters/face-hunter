import {Component, OnInit} from '@angular/core';
import {Router} from "@angular/router";
import {MatDialog} from "@angular/material/dialog";
import {InsertDialogComponent} from "../insert-dialog/insert-dialog.component";
import {HunterService} from "../services/hunter.service";
import {ToastrService} from "ngx-toastr";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {

  constructor(public dialog: MatDialog,
              private hunter: HunterService,
              private toastr: ToastrService){

  }

  insertVideo() {
    const dialogRef = this.dialog.open(InsertDialogComponent, {
      width: '500px',
      data: {}
    });

    dialogRef.afterClosed().subscribe(query_data => {
      if (query_data != null) {
        console.log(query_data);
        this.hunter.insert_video(query_data).subscribe(data => {
          this.toastr.success('Insertion started!', '', {positionClass: 'toast-bottom-right'})
        });
      }
    });
  }

}
