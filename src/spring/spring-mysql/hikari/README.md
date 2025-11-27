# hikari

## 监控指标

| 指标名称                                        | 类型    | 含义                                                  |
| ------------------------------------------- | ----- | --------------------------------------------------- |
| hikaricp_connections                        | gauge | Number of connections                               |
| hikaricp_connections_max                    | gauge | Max number of connections Shown as connection       |
| hikaricp_connections_min                    | gauge | Min number of connections  Shown as connection      |
| hikaricp_connections_active                 | gauge | Number of active connections                        |
| hikaricp_connections_pending                | gauge | Number of pending connections                       |
| hikaricp_connections_idle                   | gauge | Number of idle connections                          |
| hikaricp_connections_acquire_seconds_count  | count | Count of acquire connection time Shown as second    |
| hikaricp_connections_acquire_seconds_sum    | count | Sum of acquire connection time  Shown as second     |
| hikaricp_connections_acquire_seconds_max    | gauge | Max of acquire connection time  Shown as second     |
| hikaricp_connections_creation_seconds_count | count | Count of creation connection time   Shown as second |
| hikaricp_connections_creation_seconds_sum   | count | Sum of creation connection time   Shown as second   |
| hikaricp_connections_creation_seconds_max   | gauge | Max of creation connection time   Shown as second   |
| hikaricp_connections_usage_seconds_count    | count | Count of usage connection time    Shown as second   |
| hikaricp_connections_usage_seconds_sum      | count | Sum of usage connection time   Shown as second      |
| hikaricp_connections_usage_seconds_max      | gauge | Max of usage connection time    Shown as second     |
| hikaricp_connections_timeout_total          | count | Total number of timeout connections                 |

参考文档：https://docs.datadoghq.com/integrations/hikaricp/