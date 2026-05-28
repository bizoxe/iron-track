```text
iron_track=# SELECT
    name,
    CASE
        WHEN unit = '8kB' THEN round((setting::bigint * 8192) / (1024 * 1024), 2)::text || ' MB'
        WHEN unit = 'kB' THEN round(setting::bigint / 1024, 2)::text || ' MB'
        ELSE setting
    END AS display_setting,
    context
FROM
    pg_settings
WHERE
    name IN (
        'random_page_cost',
        'seq_page_cost',
        'shared_buffers',
        'effective_cache_size',
        'work_mem',
        'maintenance_work_mem',
        'min_parallel_table_scan_size',
        'min_parallel_index_scan_size'
    )
ORDER BY
    name;
             name             | display_setting |  context
------------------------------+-----------------+------------
 effective_cache_size         | 4096.00 MB      | user
 maintenance_work_mem         | 64.00 MB        | user
 min_parallel_index_scan_size | 0.00 MB         | user
 min_parallel_table_scan_size | 8.00 MB         | user
 random_page_cost             | 4               | user
 seq_page_cost                | 1               | user
 shared_buffers               | 128.00 MB       | postmaster
 work_mem                     | 4.00 MB         | user
(8 rows)


iron_track=# SELECT COUNT(*) FROM exercises;
 count
--------
 500000
(1 row)


iron_track=# SELECT COUNT(*) FROM exercises WHERE is_system_default IS FALSE;
 count
--------
 495063
(1 row)


iron_track=# SELECT COUNT(*) FROM exercises WHERE is_system_default IS TRUE;
 count 
-------
  4937
(1 row)


iron_track=# SHOW random_page_cost;
EXPLAIN (ANALYZE, BUFFERS, COSTS)
SELECT * FROM exercises
WHERE is_system_default IS TRUE;
 random_page_cost
------------------
 4
(1 row)

                                                             QUERY PLAN
------------------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on exercises  (cost=134.36..8074.02 rows=4967 width=1168) (actual time=3.210..10.746 rows=4937.00 loops=1)
   Recheck Cond: (is_system_default IS TRUE)
   Heap Blocks: exact=3835
   Buffers: shared hit=3861
   ->  Bitmap Index Scan on uq_exercise_slug  (cost=0.00..133.12 rows=4967 width=0) (actual time=1.724..1.725 rows=4937.00 loops=1)
         Index Searches: 1
         Buffers: shared hit=26
 Planning Time: 0.162 ms
 Execution Time: 11.560 ms
(9 rows)


iron_track=# SHOW random_page_cost;
EXPLAIN (ANALYZE, BUFFERS, COSTS)
SELECT * FROM exercises
WHERE is_system_default IS TRUE;
 random_page_cost
------------------
 1
(1 row)

                                                                QUERY PLAN
-------------------------------------------------------------------------------------------------------------------------------------------
 Index Scan using uq_exercise_slug on exercises  (cost=0.28..3476.65 rows=4967 width=1168) (actual time=0.036..6.846 rows=4937.00 loops=1)
   Index Searches: 1
   Buffers: shared hit=3967
 Planning Time: 0.163 ms
 Execution Time: 7.794 ms
(5 rows)
```