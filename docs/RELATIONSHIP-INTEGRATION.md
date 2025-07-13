# Relationship Extraction and Visualization Integration

**Last Updated:** 2025-01-27 15:30:00

## Overview

This document describes the comprehensive relationship extraction and visualization
system that analyzes code dependencies, inheritance hierarchies, and function calls
to provide interactive visualizations of codebase architecture.

## Core Features

### Relationship Types Supported

- **Inheritance**: Class inheritance hierarchies and method resolution order
- **Composition**: Field relationships between classes and models
- **Function Calls**: Method and function call dependencies
- **Import Dependencies**: Module import relationships and dependency graphs
- **Data Flow**: Variable usage and data transformation patterns

### Visualization Options

- **Interactive D3.js Graphs**: Dynamic network visualizations with zoom, pan, and filtering
- **Mermaid Diagrams**: Static relationship diagrams with export capabilities
- **Hierarchical Views**: Tree-based inheritance and composition displays
- **Force-Directed Networks**: Physics-based relationship layouts

## Usage Guide

### 1. Extract Relationships

```bash
# Extract comprehensive code structure and relationships
python tools/python_ast_extractor.py <your_project_root> --out code_structure.json

# Options:
# --include-tests: Include test files in analysis
# --max-depth: Limit recursion depth for large codebases
# --exclude-patterns: Skip files matching patterns
```

### 2. Import to Database

```bash
# Import extracted data to SQLite database
python api/enhanced_import.py code_structure.json --db code_intelligence.db

# Options:
# --update: Update existing records instead of creating new ones
# --validate: Perform validation checks during import
# --batch-size: Control import batch size for performance
```

### 3. Frontend Integration

```javascript
// Add visualization controls to dashboard
const visualizationControls = document.getElementById('visualization-controls');

// Create relationship graph button
const relationshipButton = document.createElement('button');
relationshipButton.textContent = 'Show Relationships';
relationshipButton.onclick = () => {
    visualizationManager.showEnhancedRelationshipsGraph({
        showInheritance: true,
        showComposition: true,
        showCalls: false,  // Can be toggled
        maxNodes: 100
    });
};

visualizationControls.appendChild(relationshipButton);
```

### 4. Advanced Configuration

```javascript
// Customize visualization appearance and behavior
const graphConfig = {
    // Node styling
    nodeStyles: {
        pydanticModel: { fill: '#e3f2fd', stroke: '#1976d2' },
        regularClass: { fill: '#f3e5f5', stroke: '#7b1fa2' },
        function: { fill: '#e8f5e8', stroke: '#2e7d32' }
    },
    
    // Layout options
    layout: {
        forceStrength: -300,
        linkDistance: 100,
        centerForce: 0.1
    },
    
    // Interaction settings
    interaction: {
        enableDrag: true,
        enableZoom: true,
        highlightOnHover: true
    }
};

visualizationManager.updateConfig(graphConfig);
```

## Technical Architecture

### Data Flow Pipeline

1. **AST Analysis**: Python code parsed using `ast` module
2. **Relationship Extraction**: Visitor pattern extracts entity relationships
3. **Data Normalization**: Structured data format for database storage
4. **Database Import**: Efficient batch import with validation
5. **API Exposure**: RESTful endpoints for dashboard consumption
6. **Visualization Rendering**: Client-side D3.js or server-side Mermaid

### Performance Optimizations

- **Incremental Updates**: Only analyze changed files
- **Caching Layer**: Redis cache for frequently accessed relationships
- **Batch Processing**: Efficient database operations for large codebases
- **Lazy Loading**: On-demand visualization rendering
- **Filtering Options**: Reduce complexity for large graphs

## Integration Benefits

- **Architecture Understanding**: Visualize complex code relationships
- **Dependency Analysis**: Identify tight coupling and circular dependencies
- **Refactoring Support**: Understand impact of changes before implementation
- **Documentation**: Auto-generated relationship documentation
- **Code Quality**: Identify architectural anti-patterns and violations

## Submodule Integration

This system is designed as a standalone submodule that can be integrated
into larger projects:

```bash
# Add as git submodule
git submodule add <repository-url> code-intelligence-dashboard

# Initialize and configure
cd code-intelligence-dashboard
pip install -r requirements.txt
python setup.py configure --project-root ../
```

## Requirements

- **Python 3.11+**: Core analysis and processing
- **D3.js v7+**: Client-side visualizations
- **SQLite**: Database storage
- **Panel**: Dashboard framework
- **Mermaid**: Diagram generation

- Class inheritance, function calls, and import dependencies visualized as interactive graphs
- Supports both Mermaid and D3.js visualizations
- Ready for submodule use in larger projects
