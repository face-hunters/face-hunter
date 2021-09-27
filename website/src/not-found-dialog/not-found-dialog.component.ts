import {Component, Inject} from "@angular/core";
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";

@Component({
  selector: 'not-found-dialog',
  templateUrl: 'not-found-dialog.component.html'
})
export class NotFoundDialogComponent {


  constructor(
    public dialogRef: MatDialogRef<NotFoundDialogComponent>) {}

  close(data: any = null): void {
    this.dialogRef.close(data);
  }

}
