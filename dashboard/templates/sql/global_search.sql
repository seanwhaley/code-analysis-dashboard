-- Global search across all entities
WITH file_results AS (
    SELECT 
        'file' as type,
        f.id,
        f.name,
        f.path,
        f.name || ' - ' || f.path as details,
        f.name as search_field
    FROM files f
    WHERE f.name LIKE '%' || $search_term || '%' 
       OR f.path LIKE '%' || $search_term || '%'
),
class_results AS (
    SELECT 
        'class' as type,
        c.id,
        c.name,
        f.path,
        'Class in ' || f.name as details,
        c.name as search_field
    FROM classes c
    JOIN files f ON c.file_id = f.id
    WHERE c.name LIKE '%' || $search_term || '%'
),
function_results AS (
    SELECT 
        'function' as type,
        func.id,
        func.name,
        f.path,
        'Function in ' || f.name as details,
        func.name as search_field
    FROM functions func
    JOIN files f ON func.file_id = f.id
    WHERE func.name LIKE '%' || $search_term || '%'
)
SELECT * FROM (
    SELECT * FROM file_results
    UNION ALL
    SELECT * FROM class_results  
    UNION ALL
    SELECT * FROM function_results
)
ORDER BY search_field
LIMIT $limit;
