import {Component, Inject} from "@angular/core";
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";

@Component({
  selector: 'sparql-dialog',
  templateUrl: 'sparql-dialog.component.html',
  styleUrls: ['./sparql-dialog.component.scss']
})
export class SparqlDialogComponent {

  query: any = {
    query: '',
    filter: ''
  };

  constructor(
    public dialogRef: MatDialogRef<SparqlDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any) {}

  close(data: any = null): void {
    this.dialogRef.close(data);
  }

}
