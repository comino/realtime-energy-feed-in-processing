CREATE DATABASE IF NOT EXISTS event;
USE event;

DROP TABLE IF EXISTS rabbit_events_view;
DROP TABLE IF EXISTS rabbit_latest_view;
DROP TABLE IF EXISTS rabbit_events;
DROP TABLE IF EXISTS rabbit_latest;
DROP TABLE IF EXISTS rabbit_queue;

CREATE TABLE rabbit_queue
(
    `t` UInt64,
    `id` UInt64,
    `v` Float32,
    `long` Float32,
    `lat` Float32
) ENGINE = RabbitMQ 
SETTINGS
    rabbitmq_host_port = 'localhost:5672',
    rabbitmq_exchange_name = 'clickhouse-exchange',
    rabbitmq_username='energy',
    rabbitmq_password='w************',
    rabbitmq_format = 'JSONEachRow',
    rabbitmq_flush_interval_ms = 250,
    rabbitmq_exchange_type = 'fanout',
    rabbitmq_num_consumers = 3,
    rabbitmq_num_queues = 3,
    rabbitmq_routing_key_list = 'data';

CREATE TABLE rabbit_events
(
    `t` UInt64,
    `id` UInt64,
    `v` Float32,
    `long` Float32,
    `lat` Float32
) ENGINE = MergeTree
ORDER BY (id, t)
SETTINGS index_granularity = 8192;

CREATE TABLE rabbit_latest
(
    `id` UInt64,
    `t` UInt64,
    `v` Float32,
    `long` Float32,
    `lat` Float32
) ENGINE = ReplacingMergeTree(t)
ORDER BY id;

CREATE MATERIALIZED VIEW rabbit_events_view TO rabbit_events
AS SELECT * FROM rabbit_queue;

CREATE MATERIALIZED VIEW rabbit_latest_view TO rabbit_latest
AS SELECT * FROM rabbit_queue;