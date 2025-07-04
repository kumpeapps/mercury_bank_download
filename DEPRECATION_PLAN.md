# Legacy Features Deprecation Plan

## Overview
This document outlines the plan to deprecate legacy features in the Mercury Bank Integration Platform and migrate to the new role-based access control system.

## Legacy Features to Deprecate

### 1. Legacy Admin User Scripts
- **Files**: `admin_user.py`, `admin_user.py.legacy`
- **Replacement**: `admin_user.py.new` (role-based system)
- **Status**: ✅ New system implemented
- **Action**: Archive legacy scripts and update references

### 2. Legacy `is_admin` Flag
- **Location**: User interface, backend logic, database fields
- **Replacement**: Role-based permissions (`admin`, `super-admin` roles)
- **Status**: ✅ New system implemented, backward compatibility maintained
- **Action**: Remove UI elements, keep database field for compatibility

### 3. Legacy MERCURY_API_KEY Environment Variable
- **Location**: Documentation, example files, setup scripts
- **Replacement**: Database-stored encrypted API keys per Mercury account
- **Status**: ✅ New system implemented
- **Action**: Remove from documentation and examples

### 4. Legacy dev.sh Commands
- **Commands**: `promote-admin`, `demote-admin`, `list-admin`
- **Replacement**: `assign-role`, `remove-role`, `list-by-role`
- **Status**: ✅ New commands implemented, legacy commands show deprecation warnings
- **Action**: Remove legacy commands after grace period

### 5. Legacy Database Creation Scripts
- **Files**: `create_table.py`, `update_schema.py`
- **Replacement**: SQLAlchemy-based migration system
- **Status**: ✅ New migration system implemented
- **Action**: Archive old scripts

### 6. Legacy Admin UI Elements
- **Location**: Admin templates (Make Admin/Remove Admin buttons)
- **Replacement**: Role management interface
- **Status**: ✅ New role management UI implemented
- **Action**: Remove legacy buttons, keep role management

### 7. Legacy Environment Variable Setup
- **Location**: Documentation, README, example files
- **Replacement**: Multi-account database configuration
- **Status**: ✅ New system documented
- **Action**: Clean up documentation

## Implementation Steps

### Phase 1: Mark as Deprecated (Current)
- ✅ Add deprecation warnings to legacy commands
- ✅ Update documentation to highlight new approaches
- ✅ Maintain backward compatibility

### Phase 2: Remove Legacy UI Elements
- Remove legacy admin promotion/demotion buttons
- Keep role management interface
- Update templates to use role-based approach only

### Phase 3: Archive Legacy Scripts
- Move legacy scripts to `archived/` directory
- Update symlinks and references
- Remove from active codebase

### Phase 4: Clean Documentation
- Remove legacy environment variables from examples
- Update setup instructions
- Remove outdated migration guides

### Phase 5: Final Cleanup
- Remove legacy command handlers from dev.sh
- Remove legacy compatibility code
- Remove archived files

## Timeline
- **Phase 1**: ✅ Complete
- **Phase 2**: Current (remove legacy UI elements)
- **Phase 3**: Next (archive legacy scripts)
- **Phase 4**: Following (clean documentation)
- **Phase 5**: Final (complete removal)

## Testing Strategy
- Verify new role-based system works correctly
- Test backward compatibility during transition
- Ensure no breaking changes for existing users
- Validate documentation accuracy

## Rollback Plan
- Keep archived scripts available for emergency rollback
- Maintain database schema compatibility
- Document rollback procedures
- Keep backup of working system

## Communication
- Update copilot instructions
- Notify users of deprecation timeline
- Provide migration guidance
- Document new best practices
