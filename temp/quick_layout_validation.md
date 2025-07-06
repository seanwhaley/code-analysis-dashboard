# 🚀 Quick Layout Validation Report

**Generated:** validate-layout-quick.py

==================================================

## 📊 Summary
- 🚨 **Errors:** 0
- ⚠️ **Warnings:** 3
- ℹ️ **Info:** 9

🟡 **STATUS: GOOD** - Consider addressing warnings for best practices

## 📄 dashboard.html

### ℹ️ Info

**grid_system** (Line 316): Grid row without immediate grid columns
💡 *Ensure grid-row contains grid-col elements*

**accessibility**: No skip-to-content links found
💡 *Add skip links for keyboard navigation*

## 📄 test-dashboard.html

### ⚠️ Warnings

**grid_system**: No USWDS grid-row containers found
💡 *Use .grid-row for layout containers*

**navigation**: No sidebar navigation found
💡 *Add .sidebar or .usa-layout-docs__sidenav for navigation*

**responsive**: No responsive utility classes found
💡 *Use tablet: and desktop: prefixes for responsive layout*

### ℹ️ Info

**navigation**: Only 0 navigation links found
💡 *Ensure sufficient navigation options for usability*

**layout_structure**: No content sections found
💡 *Organize content using .content-section classes*

**uswds_layout**: USWDS layout class .usa-layout-docs not found
💡 *Consider using .usa-layout-docs for consistent layout*

**uswds_layout**: USWDS layout class .dashboard-container not found
💡 *Consider using .dashboard-container for consistent layout*

**uswds_layout**: USWDS layout class .usa-body not found
💡 *Consider using .usa-body for consistent layout*

**accessibility**: No skip-to-content links found
💡 *Add skip links for keyboard navigation*

**accessibility**: Heading level skipped (accessibility issue)
💡 *Don't skip heading levels (h1→h2→h3, not h1→h3)*

## 🔧 Quick Fixes

### Priority 2: Address Warnings
- Add .sidebar or .usa-layout-docs__sidenav for navigation
- Use .grid-row for layout containers
- Use tablet: and desktop: prefixes for responsive layout

## 🎯 Next Steps
1. ✅ Review and address warnings for best practices
2. 🧪 Run comprehensive validation with WebDriver tests
3. 📱 Test responsive design on actual devices