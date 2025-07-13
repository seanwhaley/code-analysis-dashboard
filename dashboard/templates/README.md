# Template Organization Best Practices

This document outlines the improved template organization structure implemented in the dashboard project.

## Problems with Inline HTML/SQL

The original code had several issues:

1. **Mixed Concerns**: HTML and SQL code was embedded directly in Python files
2. **Maintainability**: Difficult to update styling or queries without touching Python code
3. **Code Clarity**: Python logic was obscured by large HTML/SQL blocks
4. **Reusability**: No way to reuse templates across different components
5. **Testing**: Hard to test templates independently of Python logic

## New Structure

```
dashboard/
├── templates/
│   ├── template_manager.py           # HTML template management
│   ├── dashboard_template_service.py # Dashboard-specific templates
│   ├── sql_template_manager.py       # SQL template management
│   ├── dashboard.css                 # Centralized styles
│   ├── header.html                   # Header template
│   ├── footer.html                   # Footer template
│   ├── error_page.html              # Error page template
│   ├── components/                   # Reusable components
│   │   ├── stats_card.html
│   │   ├── search_results_section.html
│   │   └── search_result_item.html
│   └── sql/                         # SQL query templates
│       ├── get_files_with_filters.sql
│       └── global_search.sql
```

## Benefits

### 1. Separation of Concerns

- HTML templates are in `.html` files
- SQL queries are in `.sql` files  
- CSS styles are in `.css` files
- Python code focuses on logic only

### 2. Template Management Services

- `TemplateManager`: Core template loading and rendering
- `DashboardTemplateService`: Dashboard-specific template logic
- `SQLTemplateManager`: SQL query template management

### 3. Reusability

- Templates can be reused across components
- Components can be composed from smaller templates
- SQL queries can be shared between services

### 4. Maintainability

- Easy to update styles without touching Python
- SQL queries can be optimized independently
- Templates can be tested separately

### 5. Type Safety

- Template parameters are properly typed
- Error handling for missing templates
- Validation of template variables

## Usage Examples

### HTML Templates

```python
from dashboard.templates.template_manager import render_header, render_footer

# Simple template rendering
header_html = render_header()
footer_html = render_footer()

# Template with parameters
error_html = render_error_page(error="Database not found", db_path="/path/to/db")
```

### Dashboard Templates

```python
from dashboard.templates.dashboard_template_service import dashboard_template_service

# Status messages
status_html = dashboard_template_service.render_status_message(
    "Analysis completed successfully!", "success"
)

# Stats cards
stats_html = dashboard_template_service.render_stats_cards_row(system_stats)

# Search results
results_html = dashboard_template_service.render_search_results(results, "search_term")
```

### SQL Templates

```python
from dashboard.templates.sql_template_manager import sql_template_manager

# Parameterized queries
files_query = sql_template_manager.render_files_query(
    domain="web_development",
    file_type="python",
    min_lines=100,
    limit=50
)

search_query = sql_template_manager.render_global_search_query(
    search_term="User",
    limit=25
)
```

## Best Practices

### 1. Template Organization

- Keep templates small and focused
- Use component composition for complex UI
- Group related templates in subdirectories

### 2. Parameter Handling

- Always provide default values for optional parameters
- Validate parameters before rendering
- Use type hints for template functions

### 3. Error Handling

- Graceful degradation when templates are missing
- Log template loading errors
- Return fallback content instead of crashing

### 4. Performance

- Cache loaded templates in memory
- Provide cache clearing functionality
- Use lazy loading for large template sets

### 5. Security

- Escape user input in templates
- Sanitize SQL parameters
- Use parameterized queries to prevent injection

## Migration Strategy

### Phase 1: Create Template Infrastructure ✅

- Set up template directories
- Create template manager services
- Implement basic templates

### Phase 2: Migrate Critical Components (In Progress)

- Move header/footer to templates
- Convert error pages
- Update statistics displays

### Phase 3: Component Templates

- Break down complex components
- Create reusable sub-components
- Implement composition patterns

### Phase 4: SQL Template Migration

- Extract SQL queries to files
- Implement parameterized query system
- Add query optimization and validation

### Phase 5: Advanced Features

- Template inheritance
- Conditional rendering
- Internationalization support

## Configuration

Templates can be configured through the dashboard settings:

```yaml
ui:
  template_dir: "custom/templates"
  cache_templates: true
  template_debug: false
```

This approach provides a scalable, maintainable foundation for template management while maintaining the flexibility to extend and customize as needed.
