-- Get file statistics with filtering
SELECT 
    f.id,
    f.name,
    f.path,
    f.domain,
    f.file_type,
    f.complexity_level,
    f.lines_of_code,
    COUNT(DISTINCT c.id) as classes_count,
    COUNT(DISTINCT func.id) as functions_count
FROM files f
LEFT JOIN classes c ON f.id = c.file_id
LEFT JOIN functions func ON f.id = func.file_id
WHERE 1=1
    AND ($domain IS NULL OR f.domain = $domain)
    AND ($file_type IS NULL OR f.file_type = $file_type)
    AND ($complexity_level IS NULL OR f.complexity_level = $complexity_level)
    AND ($min_lines IS NULL OR f.lines_of_code >= $min_lines)
    AND ($max_lines IS NULL OR f.lines_of_code <= $max_lines)
    AND ($search_term IS NULL OR f.name LIKE '%' || $search_term || '%' OR f.path LIKE '%' || $search_term || '%')
GROUP BY f.id, f.name, f.path, f.domain, f.file_type, f.complexity_level, f.lines_of_code
ORDER BY f.name
LIMIT $limit;
