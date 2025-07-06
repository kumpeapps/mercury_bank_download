# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-01-06

### Added
- **Complete Budget Management System** - Full-featured budget creation, editing, and tracking
- **Advanced Budget Reports** - Detailed budget vs. actual spending analysis with drill-down capability
- **Budget Analytics Integration** - Visual budget charts integrated with main reports dashboard  
- **Category-Based Budgeting** - Set spending limits by transaction categories with sub-category support
- **Multi-Account Budget Support** - Create budgets spanning multiple Mercury accounts within a group
- **Smart Budget Progress Tracking** - Real-time progress calculations with color-coded status indicators
- **Budget Copy Functionality** - Easy month-to-month budget planning with one-click copying
- **Role-Based Budget Access** - Budget management restricted to users with appropriate permissions
- **Interactive Budget Reports** - Transaction-level drill-down and variance analysis

### Database Changes
- **New Tables**: `budgets`, `budget_categories`, `budget_accounts`
- **Migration**: `b5ed68a6aa24_add_budgets_and_budget_categories_.py`
- **New Role**: `budgets` role for budget management permissions
- **Foreign Key Constraints**: Proper referential integrity with existing user and account tables
- **Indexes**: Automatic indexes on foreign key columns for performance

### Enhanced
- **Web Interface Navigation** - Added "Budgets" menu item for budget management access
- **Reports Dashboard** - Integrated budget analytics with existing expense and category charts
- **User Role System** - Added budget-specific permissions and access controls
- **Documentation** - Comprehensive budget usage guide and database migration documentation

## [2.0.1] - 2025-01-05

### Added
- Enhanced chart controls in reports page with category/sub-category toggle
- Dynamic chart title updates based on selected view mode
- Improved user experience with cleaner, simplified chart views by default

### Changed
- Reports now show main categories by default instead of sub-categories
- Sub-categories can be enabled via checkbox toggle in chart options
- Both Budget Analysis and Expense Breakdown charts respect the same toggle setting

### Improved
- More intuitive financial reporting with drill-down capability
- Better chart readability with main category aggregation
- Consistent behavior across all chart types

## [2.0.0] - 2024-12-xx

### Added
- Mercury Account User Management through CLI interface
- Enhanced CLI interface with additional management features
- Comprehensive testing framework with 38 test cases
- Role-based access control improvements
- Complete CLI documentation and improved README

### Changed
- Strengthened security with enhanced role-based permissions
- Improved user management system
- Enhanced Docker deployment workflow

### Fixed
- Various security improvements and bug fixes
- Database migration consistency
- Error handling and recovery mechanisms

## [1.x] - Previous Versions

### Features
- Initial Mercury Bank API integration
- Basic transaction synchronization
- Web interface for data management
- Docker containerization
- User authentication system
