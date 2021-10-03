import {Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";

@Injectable()
export class YamlService {
  constructor(private http: HttpClient) { }

  public fetchYaml(fileName: string) {
    return this.http.get(`/assets/${fileName}`, { responseType: 'text' })
  }
}
