-- File: test_kd_tree.sql
-- Unit test for kd_tree.sql_in


-- Create a test dataset.
CREATE TEMP TABLE kdtree_test_data (id INT, dimension INT, val FLOAT8) DISTRIBUTED RANDOMLY;
INSERT INTO kdtree_test_data VALUES
(1, 1, 0),  
(1, 2, 1),
(2, 1, 2),
(2, 2, 2),
(3, 1, 3),
(3, 2, 6),
(4, 1, 4),
(4, 2, 9),
(5, 1, 5),
(5, 2, 7),
(6, 1, 6),
(6, 2, 2),
(7, 1, 7),
(7, 2, 3),
(8, 1, 8),
(8, 2, 4),
(9, 1, 9),
(9, 2, 7),
(10, 1, 10),
(10, 2, 8); 


-- Construct a KD-tree with each leaf node containing no more than 3 data points.
SELECT PDLTOOLS_SCHEMA.kd_tree('kdtree_test_data', 'id', 'dimension', 'val', 3, 'kdtree_test_output'); 


-- Check if the KD-tree is correctly constructed.
CREATE TEMP TABLE correct_kdtree_test_output (node_location INT[], split_dimension INT, split_value FLOAT8, pop_variance FLOAT8, leaf_member INT[]) DISTRIBUTED RANDOMLY;
INSERT INTO correct_kdtree_test_output VALUES
(ARRAY[0],2,6,9.2,NULL),  
(ARRAY[0,0],NULL,NULL,NULL,ARRAY[1,2,3]),  
(ARRAY[0,1],NULL,NULL,NULL,ARRAY[4,5]),  
(ARRAY[1],2,4,5.36,NULL),  
(ARRAY[1,0],NULL,NULL,NULL,ARRAY[6,7,8]),  
(ARRAY[1,1],NULL,NULL,NULL,ARRAY[9,10]),  
(NULL,1,5, 9.24, NULL);

SELECT PDLTOOLS_SCHEMA.assert(count::TEXT, '0'::TEXT)
FROM (
    SELECT count(*) FROM (
        SELECT * FROM kdtree_test_output
        EXCEPT
        SELECT * FROM correct_kdtree_test_output
    ) foo
) foo;



-- Find the 2-nearest neighbours for a test point (3.5,4).

SELECT PDLTOOLS_SCHEMA.assert(array_to_string(result,','), '3,2,2.06,2.50'::TEXT)
FROM (
    SELECT array_agg(knn_id ORDER BY knn_dist)::NUMERIC[]|| array_agg(knn_dist ORDER BY knn_dist) result
    FROM (
        SELECT unnest(knn_id) knn_id, round(unnest(knn_dist)::NUMERIC,2) knn_dist 
        FROM PDLTOOLS_SCHEMA.kdtree_knn('kdtree_test_data', 'id', 'dimension', 'val', 'kdtree_test_output', array[3.5,4], 2)
    ) foo
) foo;



-- Find the 2-nearest neighbours for multiple test points that are stored in a table.
 
CREATE TEMP TABLE kdtree_knn_query_data (query_id INT, query_point FLOAT8[]) DISTRIBUTED RANDOMLY;
INSERT INTO kdtree_knn_query_data VALUES
(1, array[8,1]), 
(2, array[3,4]),
(3, array[1,2.5]);

SELECT PDLTOOLS_SCHEMA.kdtree_knn('kdtree_test_data', 'id', 'dimension', 'val', 'kdtree_test_output',
                                  'kdtree_knn_query_data', 'query_id', 'query_point', 2, 'query_result');

                      
SELECT PDLTOOLS_SCHEMA.assert(array_to_string(all_result,','), '1,6,7,2.24,2.24,2,3,2,2.00,2.24,3,2,1,1.12,1.80'::TEXT)
FROM (
    SELECT array_agg(result ORDER BY result) all_result
    FROM (
        SELECT array_to_string(ARRAY[query_id]::NUMERIC[] || array_agg(knn_id ORDER BY knn_dist,knn_id)::NUMERIC[] || array_agg(knn_dist ORDER BY knn_dist), ',') result
        FROM (
            SELECT query_id, unnest(knn_id) knn_id, round(unnest(knn_dist)::NUMERIC,2) knn_dist 
            FROM query_result
        ) foo
        GROUP BY query_id
    ) foo
) foo;
      

-- Clean up temp tables.
DROP TABLE kdtree_test_data;
DROP TABLE kdtree_test_output;
DROP TABLE correct_kdtree_test_output;
DROP TABLE kdtree_knn_query_data;




