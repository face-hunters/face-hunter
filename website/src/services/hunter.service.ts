import {HttpClient} from "@angular/common/http";
import {Injectable} from "@angular/core";


@Injectable()
export class HunterService {

  constructor(
    private http: HttpClient
  ) { }

  get_scenes_of_entity(name: string) {
    return this.http.get<any>('http://localhost:5000/api/entity/' + name);
  }

  execute_query(query: string) {
    return this.http.post<any>('http://localhost:5000/api/query', query)
  }

}
