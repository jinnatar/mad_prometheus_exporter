# MAD Prometheus Exporter

Very much still a work in progress but exports some basic metrics that the author finds useful. If more metrics are desired, feel free to open an issue on GitHub.

## Currently supported metrics

- mad_area_count{type}
- mad_area_pokestop_count{area}
- mad_area_quest_count{area}
- mad_device_count
- mad_device_injection_status{origin, scanmode}
- mad_device_latest_data_timestamp{origin, scanmode}

## Installation

1. `pip install -r requirements.txt`
2. Install the plugin however you usually install plugins.
3. Restart MAD.
4. Visit `http://127.0.0.1:5000/metrics` (Or whereever you serve the MADMin interface.)
5. If you want, use that URL to ingest the data into Prometheus.

## Example Prometheus scrape config

```
- job_name: 'MAD'
      scrape_interval: 10s
      metrics_path: /metrics
      static_configs:
        - targets: ['127.0.0.1:5000']
```

## Current metrics provided with example data

First there's automatic metrics from the running Python instance but further down are the MAD specific metrics.

```
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 8.70676e+06
python_gc_objects_collected_total{generation="1"} 4.523287e+06
python_gc_objects_collected_total{generation="2"} 6.026616e+06
# HELP python_gc_objects_uncollectable_total Uncollectable object found during GC
# TYPE python_gc_objects_uncollectable_total counter
python_gc_objects_uncollectable_total{generation="0"} 0.0
python_gc_objects_uncollectable_total{generation="1"} 0.0
python_gc_objects_uncollectable_total{generation="2"} 0.0
# HELP python_gc_collections_total Number of times this generation was collected
# TYPE python_gc_collections_total counter
python_gc_collections_total{generation="0"} 6.3282832e+07
python_gc_collections_total{generation="1"} 5.752984e+06
python_gc_collections_total{generation="2"} 108533.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="7",patchlevel="12",version="3.7.12"} 1.0
# HELP process_virtual_memory_bytes Virtual memory size in bytes.
# TYPE process_virtual_memory_bytes gauge
process_virtual_memory_bytes 3.371814912e+09
# HELP process_resident_memory_bytes Resident memory size in bytes.
# TYPE process_resident_memory_bytes gauge
process_resident_memory_bytes 8.87607296e+08
# HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
# TYPE process_start_time_seconds gauge
process_start_time_seconds 1.64007030963e+09
# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 194053.92
# HELP process_open_fds Number of open file descriptors.
# TYPE process_open_fds gauge
process_open_fds 72.0
# HELP process_max_fds Maximum number of open file descriptors.
# TYPE process_max_fds gauge
process_max_fds 1.048576e+06
# HELP mad_area_count Number of areas defined
# TYPE mad_area_count gauge
mad_area_count{type="pokestops"} 6.0
# HELP mad_area_pokestop_count Number of pokestops
# TYPE mad_area_pokestop_count gauge
mad_area_pokestop_count{area="city1_area"} 481.0
mad_area_pokestop_count{area="town1_quest_area"} 259.0
mad_area_pokestop_count{area="village1_quest_area"} 6.0
# HELP mad_area_quest_count Number of quests
# TYPE mad_area_quest_count gauge
mad_area_quest_count{area="city1_area"} 146.0
mad_area_quest_count{area="town1_area"} 16.0
mad_area_quest_count{area="village1_area"} 0.0
# HELP mad_device_count Number of defined device origins
# TYPE mad_device_count gauge
mad_device_count 4.0
# HELP mad_device_injection_status Boolean for whether injection is active
# TYPE mad_device_injection_status gauge
mad_device_injection_status{origin="atv02",scanmode="quests"} 1.0
mad_device_injection_status{origin="atv03",scanmode="quests"} 1.0
mad_device_injection_status{origin="atv04",scanmode="quests"} 1.0
# HELP mad_device_latest_data_timestamp Timestamp of latest data received from device
# TYPE mad_device_latest_data_timestamp gauge
mad_device_latest_data_timestamp{origin="atv01",scanmode="raids"} 1.6415454424132838e+09
mad_device_latest_data_timestamp{origin="atv02",scanmode="quests"} 1.641545517e+09
mad_device_latest_data_timestamp{origin="atv03",scanmode="quests"} 1.641545517e+09
mad_device_latest_data_timestamp{origin="atv04",scanmode="quests"} 1.641545518e+09
```
