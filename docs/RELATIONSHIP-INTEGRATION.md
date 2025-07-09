# Relationship Extraction and Visualization Integration

## Usage

1. **Extract Relationships**
   ```bash
   python tools/python_ast_extractor.py <your_project_root> --out code_structure.json
   ```

2. **Import to Database**
   ```bash
   python api/enhanced_import.py code_structure.json --db documentation.db
   ```

3. **Frontend**
   - Add a button to dashboard to call `visualizationManager.showEnhancedRelationshipsGraph()`
   - Ensure `d3-visualizer.js` is loaded in dashboard.

## Features

- Class inheritance, function calls, and import dependencies visualized as interactive graphs
- Supports both Mermaid and D3.js visualizations
- Ready for submodule use in larger projects