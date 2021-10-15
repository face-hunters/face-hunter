import {HttpClient} from "@angular/common/http";
import {Injectable} from "@angular/core";
import {YamlService} from "./yaml.service";


@Injectable()
export class HunterService {

  base_url = 'http://localhost:5000'

  constructor(
    private http: HttpClient,
    private yaml: YamlService
  ) {
    yaml.fetchYaml('config.yaml').subscribe(response => {
      let lines: string[] = response.split('\n');  // create array where each YAML line is one entry
      let object: any = {};
      lines.forEach((line: string) => {
        let delimiter = line.indexOf(':');  // find the colon position inside the line string
        let key = line.substr(0, delimiter);  // extract the key (everything before the colon)
        let value = line.substr(delimiter + 2);  // extract the value (everything after the colon)
        object[key] = value;  // add a new key-value pair to the object
      this.base_url = object['endpoint'] + ':' + object['port'];
      })});
  }

  get_scenes_of_entity(name: string) {
    return this.http.get<any>( this.base_url + '/api/entity/' + name);
  }

  execute_query(query: string) {
    return this.http.post<any>(this.base_url + '/api/query', query)
  }

  insert_video(id: string) {
    return this.http.get<any>( this.base_url + '/api/youtube/' + id);
  }

}
