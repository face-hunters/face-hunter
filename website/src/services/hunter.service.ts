import {HttpClient} from "@angular/common/http";
import {Injectable} from "@angular/core";


@Injectable()
export class HunterService {

  constructor(
    private http: HttpClient
  ) { }

  get_scenes_of_entity(name: string) {
    return name;
  }

}
