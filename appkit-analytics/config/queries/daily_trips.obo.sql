-- Runs on behalf of the signed-in user (.obo.sql), so Unity Catalog permissions and audit apply to them.
-- Source: Databricks sample dataset samples.nyctaxi.trips (Jan–Feb 2016).
-- @param min_distance INT = 0
SELECT
  DATE(tpep_pickup_datetime) AS pickup_date,
  COUNT(*) AS trips,
  ROUND(AVG(fare_amount), 2) AS avg_fare
FROM samples.nyctaxi.trips
WHERE trip_distance >= :min_distance
GROUP BY ALL
ORDER BY pickup_date;
