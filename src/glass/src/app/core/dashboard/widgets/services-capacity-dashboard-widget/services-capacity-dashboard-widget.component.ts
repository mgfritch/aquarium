import { Component } from '@angular/core';
import * as _ from 'lodash';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { ServicesService, ServiceStorage } from '~/app/shared/services/api/services.service';

@Component({
  selector: 'glass-services-capacity-dashboard-widget',
  templateUrl: './services-capacity-dashboard-widget.component.html',
  styleUrls: ['./services-capacity-dashboard-widget.component.scss']
})
export class ServicesCapacityDashboardWidgetComponent {
  chartData: any[] = [];
  colorScheme = {
    domain: ['#00739c', '#fa9334', '#b54236', '#1c445c', '#00aab4']
  };

  constructor(private servicesService: ServicesService) {}

  loadData(): Observable<Array<ServiceStorage>> {
    return this.servicesService.stats().pipe(
      map((data: Record<string, ServiceStorage>): ServiceStorage[] => {
        let result: ServiceStorage[] = _.values(data);
        result = _.orderBy(result, ['used'], ['desc']);
        return _.take(result, 5);
      })
    );
  }

  updateChartData(data: ServiceStorage[]) {
    this.chartData = _.map(data, (serviceStorage: ServiceStorage) => ({
      name: serviceStorage.name,
      value: serviceStorage.used
    }));
  }

  dataLabelFormatting(value: number): string {
    // Note, this implementation is by intention, do NOT use code like
    // 'dataLabelFormatting.bind(this)' in the template, otherwise this
    // method is called over and over again because Angular CD seems to
    // assume something has been changed.
    const pipe = new BytesToSizePipe();
    return pipe.transform(value);
  }
}
