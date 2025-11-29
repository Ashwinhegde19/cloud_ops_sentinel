# Implementation Plan

- [x] 1. Set up database and core models
  - [x] 1.1 Create SQLite database schema with users, sessions, platforms, api_keys tables
    - Create `app/database.py` with SQLAlchemy models
    - Initialize database on first run
    - _Requirements: 1.2, 3.3, 4.2_
  - [x] 1.2 Add Pydantic models for User, Session, Platform, ApiKey, ApiKeyInfo
    - Add to `app/models.py`
    - _Requirements: 1.2, 3.2, 4.1_
  - [x]* 1.3 Write property test for data model validation
    - **Property 1: Password Hash Irreversibility**
    - **Validates: Requirements 1.2**

- [x] 2. Implement authentication module
  - [x] 2.1 Create `app/auth.py` with password hashing using bcrypt
    - Implement `hash_password()` and `verify_password()`
    - _Requirements: 1.2_
  - [x] 2.2 Implement session management
    - Implement `create_session()`, `validate_session()`, `logout()`
    - Sessions expire after 24 hours
    - _Requirements: 1.2, 1.4, 1.5_
  - [x] 2.3 Implement `authenticate()` function
    - Verify credentials, return generic error for invalid attempts
    - _Requirements: 1.2, 1.3_
  - [x]* 2.4 Write property tests for authentication
    - **Property 2: Invalid Credentials Generic Error**
    - **Property 3: Session Logout Invalidation**
    - **Validates: Requirements 1.3, 1.4**

- [x] 3. Implement permissions module
  - [x] 3.1 Create `app/permissions.py` with role definitions
    - Define viewer, operator, admin permission sets
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 3.2 Implement permission checking functions
    - `check_permission()`, `require_role()` decorator, `get_user_permissions()`
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x]* 3.3 Write property tests for permissions
    - **Property 4: Role Permission Hierarchy**
    - **Property 5: Non-Admin Access Denial**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement platform management
  - [x] 5.1 Create `app/platforms.py` with encryption utilities
    - Use Fernet symmetric encryption for credentials
    - Implement `encrypt_credentials()`, `decrypt_credentials()`
    - _Requirements: 3.3_
  - [x] 5.2 Implement platform CRUD operations
    - `list_platforms()`, `add_platform()`, `update_platform()`, `delete_platform()`
    - _Requirements: 3.1, 3.2, 3.5_
  - [x] 5.3 Implement connection testing
    - `test_connection()` for AWS, GCP, Azure, Custom
    - _Requirements: 3.4_
  - [x]* 5.4 Write property tests for platform management
    - **Property 6: Credential Encryption**
    - **Property 7: Platform Deletion Cleanup**
    - **Validates: Requirements 3.3, 3.5**

- [x] 6. Implement API key management
  - [x] 6.1 Create `app/api_keys.py` with key operations
    - `list_keys()`, `add_key()`, `update_key()`, `delete_key()`, `get_key()`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [x] 6.2 Implement key masking
    - `mask_key()` shows only last 4 characters
    - _Requirements: 4.1_
  - [x]* 6.3 Write property tests for API keys
    - **Property 8: API Key Masking**
    - **Property 9: API Key Encryption Round-Trip**
    - **Validates: Requirements 4.1, 4.2, 4.5**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement settings UI
  - [x] 8.1 Create `app/settings_ui.py` with tabbed interface
    - Profile tab for all users
    - Platforms tab for admins
    - API Keys tab for admins
    - _Requirements: 5.2_
  - [x] 8.2 Implement profile settings
    - Update email, change password
    - _Requirements: 5.3_
  - [x] 8.3 Implement platform configuration forms
    - Forms for AWS, GCP, Azure, Custom platforms
    - _Requirements: 5.4_
  - [x] 8.4 Implement API key management UI
    - Add, update, delete keys with masked display
    - _Requirements: 4.1, 5.2_
  - [x]* 8.5 Write property test for settings visibility
    - **Property 10: Settings Tab Visibility**
    - **Validates: Requirements 5.2**

- [x] 9. Integrate authentication with main UI
  - [x] 9.1 Add Gradio authentication to main app
    - Wrap existing UI with login requirement
    - Add settings icon to header
    - _Requirements: 1.1, 5.1_
  - [x] 9.2 Add role-based feature gating
    - Gate restart operations for operators+
    - Gate admin features for admins only
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 9.3 Create default admin user on first run
    - Username: admin, prompt for password
    - _Requirements: 1.2_

- [x] 10. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

