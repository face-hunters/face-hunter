import {Component, Inject} from "@angular/core";
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";

@Component({
  selector: 'insert-dialog',
  templateUrl: 'insert-dialog.component.html',
  styleUrls: ['./insert-dialog.component.scss']
})
export class InsertDialogComponent {

  youtubeId: string = '';

  constructor(
    public dialogRef: MatDialogRef<InsertDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any) {}

  close(data: any = null): void {
    this.dialogRef.close(data);
  }

}
