import {
  LineChart,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@databricks/appkit-ui/react';
import { sql } from '@databricks/appkit-ui/js';
import { useState } from 'react';

const DISTANCES = [0, 1, 2, 5, 10];

export function AnalyticsPage() {
  const [minDistance, setMinDistance] = useState(0);
  const parameters = { min_distance: sql.int(minDistance) };

  return (
    <div className="space-y-6 w-full max-w-7xl mx-auto">
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>Daily NYC taxi trips, Jan–Feb 2016</CardTitle>
          <CardDescription>
            Source: samples.nyctaxi.trips (Databricks sample data). Queries run as you, so Unity Catalog
            permissions apply.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="max-w-xs space-y-2">
            <Label htmlFor="min-distance">Minimum trip distance (miles)</Label>
            <Select value={String(minDistance)} onValueChange={(v) => setMinDistance(Number(v))}>
              <SelectTrigger id="min-distance">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DISTANCES.map((d) => (
                  <SelectItem key={d} value={String(d)}>
                    {d === 0 ? 'All trips' : `${d}+ miles`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <LineChart queryKey="daily_trips" parameters={parameters} xKey="pickup_date" yKey="trips" />
        </CardContent>
      </Card>
    </div>
  );
}
