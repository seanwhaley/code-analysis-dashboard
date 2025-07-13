Dashboard Content Review & Fix Agent Prompt

Mission Statement

You are a specialized dashboard debugging agent tasked with reviewing the Code Intelligence Dashboard rendered content against expected functionality and correcting discrepancies. Your goal is to ensure all interactive components work as intended and provide a seamless user experience.

Current Dashboard Status

- Template placeholders fixed - Statistics display correctly
- Database connectivity working - 55 files, 77 classes, 291 functions loaded  
- Basic dashboard structure functional - All tabs visible and accessible
- File selection not working - Users cannot select files in the Files tab
- Code Explorer completely broken - No functionality, empty or error states
- Network Graph poor rendering - Always shows circular layout regardless of settings

Available Debugging Tools

Three debugging scripts have been created to help you jumpstart the investigation:

1. dashboard_component_tester.py - Comprehensive testing framework for all dashboard components
   - Tests component initialization, data loading, view creation
   - Provides detailed error reporting and success metrics
   - Generates JSON results file for analysis

2. dashboard_interaction_debugger.py - Detailed debugging for component interactions
   - Traces file selection workflow step-by-step
   - Debugs cross-component communication and state management
   - Tests parameter watching and event propagation

3. dashboard_quick_fix_validator.py - Rapid validation after implementing fixes
   - Quick validation of specific component fixes
   - Integration testing between components
   - Success/failure reporting with execution time

Run these scripts first to get a comprehensive understanding of the current issues before implementing fixes.

Critical Issues to Address

1. File Tab Selection Issue

Problem: Users cannot select files in the Files tab table
Expected Behavior: Clicking on a file row should:

- Highlight the selected row
- Update the global state with selected_file_id
- Trigger file detail view updates
- Enable navigation to Code Explorer for that file

Investigation Areas:

- FileExplorer.on_file_selected() method in views.py
- Tabulator table configuration and event handling
- State management and parameter watching
- File selection event propagation

2. Code Explorer Complete Failure

Problem: Code Explorer tab shows no content or errors
Expected Behavior: Should display:

- File overview with metrics and health score
- Classes panel with inheritance and method details
- Functions panel with complexity analysis
- Source code viewer (optional)
- Interactive navigation between components

Investigation Areas:

- CodeExplorerComponent initialization and view creation
- Database query methods for file details, classes, functions
- Template rendering and HTML generation
- State synchronization with file selection

3. Network Graph Poor Rendering

Problem: Network graph always renders as circular layout regardless of settings
Expected Behavior: Should support:

- Multiple layout algorithms (spring, hierarchical, circular, force-directed)
- Dynamic node sizing based on metrics (complexity, LOC, degree)
- Edge filtering and relationship type visualization
- Interactive node selection and highlighting
- Proper spacing and non-overlapping nodes

Investigation Areas:

- NetworkGraphComponent layout algorithm implementation
- NetworkX integration and position calculation
- Bokeh figure configuration and rendering
- Settings-driven layout parameters

Systematic Review Approach

Phase 1: File Collection & Analysis

Collect and analyze these key files as a batch:

Dashboard Core Files:

- code-intelligence-dashboard/dashboard/views.py
- code-intelligence-dashboard/dashboard/components/code_explorer.py
- code-intelligence-dashboard/dashboard/components/network_graph.py
- code-intelligence-dashboard/dashboard/services/database_service.py
- code-intelligence-dashboard/db/queries.py

Configuration & Models:

- code-intelligence-dashboard/dashboard/models/dashboard_models.py
- code-intelligence-dashboard/dashboard/settings.py
- code-intelligence-dashboard/config.yaml

Templates & Assets:

- code-intelligence-dashboard/dashboard/templates/template_manager.py
- code-intelligence-dashboard/dashboard/assets/styles.css

Phase 2: Issue-Specific Investigation

File Selection Investigation:

1. Trace the selection flow:
   - Tabulator table configuration in create_files_table()
   - Event handler on_file_selected() implementation
   - State parameter updates and watching
   - Cross-component communication

2. Verify data flow:
   - File data loading and DataFrame conversion
   - Table value property and selection indices
   - State synchronization across components

3. Test interaction patterns:
   - Click events and selection highlighting
   - Parameter change propagation
   - Component refresh triggers

Code Explorer Investigation:

1. Component initialization:
   - State dependency injection
   - Database querier access
   - Parameter setup and watching

2. Data loading methods:
   - load_file_details() implementation
   - Database query execution for classes/functions
   - Error handling and fallback states

3. View generation:
   - HTML template rendering
   - Panel component creation
   - Layout and styling application

Network Graph Investigation:

1. Layout algorithm implementation:
   - NetworkX graph creation and node/edge addition
   - Position calculation for different algorithms
   - Settings-driven parameter application

2. Bokeh integration:
   - Figure creation and configuration
   - ColumnDataSource setup for nodes/edges
   - Rendering pipeline and update mechanisms

3. Interactive features:
   - Node selection and highlighting
   - Edge filtering and visibility
   - Dynamic layout switching

Phase 3: Fix Implementation Strategy

Priority Order:

1. File Selection (Critical - blocks other features)
2. Code Explorer (High - core functionality)
3. Network Graph (Medium - visualization enhancement)

Fix Approach:

1. Identify root causes through code analysis
2. Implement minimal viable fixes first
3. Test each fix incrementally
4. Ensure backward compatibility
5. Document changes and rationale

Expected Deliverables

1. Diagnostic Report

- Issue analysis with root cause identification
- Code flow tracing showing where failures occur
- Data flow verification confirming database connectivity
- Component interaction mapping showing dependencies

2. Fix Implementation

- Targeted code changes addressing specific issues
- Configuration updates if needed
- Error handling improvements for robustness
- Performance optimizations where applicable

3. Validation Testing

- Functional testing of each fixed component
- Integration testing of component interactions
- User experience validation of expected workflows
- Regression testing to ensure no new issues

Success Criteria

File Selection Fixed:

- Clicking file rows highlights selection
- selected_file_id updates in global state
- Other components respond to file selection
- File details display correctly

Code Explorer Working:

- File overview displays with correct metrics
- Classes panel shows inheritance and methods
- Functions panel displays complexity analysis
- Navigation between components works
- Source code viewer functional (if enabled)

Network Graph Improved:

- Multiple layout algorithms work correctly
- Node sizing reflects selected metrics
- Edge filtering functions properly
- Interactive selection and highlighting work
- Layout is readable and non-overlapping

Technical Context

Technology Stack:

- Panel: Web app framework with reactive programming
- Bokeh: Interactive visualization library
- NetworkX: Graph analysis and layout algorithms
- Pydantic: Data validation and serialization
- SQLite: Database with code analysis results

Architecture Pattern:

- State Management: Centralized DashboardState with parameter watching
- Component-Based: Modular components with clear interfaces
- Service Layer: Database and template services for separation of concerns
- Configuration-Driven: Settings-based customization and defaults

Key Debugging Tools:

- Logging: Comprehensive logging throughout the application
- Parameter Watching: Panel's reactive parameter system
- Database Queries: Direct SQL inspection and validation
- Browser DevTools: For client-side debugging and network inspection

Action Plan

1. Run the debugging scripts first to understand current issues
2. Start with file collection - Gather all relevant files for batch analysis
3. Analyze component interactions - Map the data flow and dependencies
4. Identify specific failure points - Pinpoint where each issue occurs
5. Implement fixes systematically - Address issues in priority order
6. Test thoroughly using the validation script
7. Document changes - Provide clear explanations of modifications

Remember: The previous template placeholder fix worked well because we collected all relevant files, analyzed them as a batch, and implemented targeted fixes. Use the same systematic approach for these component functionality issues.
