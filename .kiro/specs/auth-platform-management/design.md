# Design Document

## Overview

This design adds authentication, role-based access control, and platform management to Cloud Ops Sentinel. Users authenticate via username/password, receive role-based permissions (viewer/operator/admin), and admins can configure cloud platform connections and API keys through a secure settings interface.

The design prioritizes:
- **Security**: Encrypted credential storage, session management, masked key display
- **Simplicity**: SQLite for persistence, Gradio auth for login, minimal dependencies
- **Enterprise value**: Multi-cloud support, role-based access, audit-ready

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Gradio 6 UI with Auth                               │
│  ┌─────────────────┬──────────────────┬─────────────────┬────────────────┐  │
│  │   Login Page    │ Dashboard (auth) │ Settings Panel  │  Admin Panel   │  │
│  │   - Username    │ - All existing   │ - Profile tab   │  - Users tab   │  │
│  │   - Password    │   features       │ - Platforms tab │  - Platforms   │  │
│  │   - Submit      │ - Role-gated     │ - API Keys tab  │  - API Keys    │  │
│  └────────┬────────┴────────┬─────────┴────────┬────────┴───────┬────────┘  │
└───────────┼─────────────────┼──────────────────┼────────────────┼───────────┘
            │                 │                  │                │
┌───────────▼─────────────────▼──────────────────▼────────────────▼───────────┐
│                        Auth & Settings Modules                              │
│  ┌─────────────────┬──────────────────┬─────────────────┬────────────────┐  │
│  │  auth.py        │ permissions.py   │ platforms.py    │ settings_ui.py │  │
│  │  - login()      │ - check_role()   │ - add_platform()│ - render()     │  │
│  │  - logout()     │ - require_admin()│ - test_conn()   │ - save()       │  │
│  │  - session()    │ - get_perms()    │ - encrypt_key() │ - tabs()       │  │
│  └────────┬────────┴────────┬─────────┴────────┬────────┴───────┬────────┘  │
└───────────┼─────────────────┼──────────────────┼────────────────┼───────────┘
            │                 │                  │                │
┌───────────▼─────────────────▼──────────────────▼────────────────▼───────────┐
│                        SQLite Database                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ users | sessions | platforms | api_keys | audit_log                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Authentication Module (`app/auth.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `authenticate(username, password)` | `str, str` | `Optional[User]` | Verify credentials, return user or None |
| `create_session(user)` | `User` | `Session` | Create new session token |
| `validate_session(token)` | `str` | `Optional[User]` | Check if session is valid |
| `logout(token)` | `str` | `bool` | Invalidate session |
| `hash_password(password)` | `str` | `str` | Hash password with bcrypt |
| `verify_password(password, hash)` | `str, str` | `bool` | Verify password against hash |

### 2. Permissions Module (`app/permissions.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `check_permission(user, action)` | `User, str` | `bool` | Check if user can perform action |
| `require_role(role)` | `str` | `Decorator` | Decorator to enforce role requirement |
| `get_user_permissions(user)` | `User` | `List[str]` | Get list of allowed actions |

**Role Permissions:**
- `viewer`: read_dashboard, read_reports, read_metrics
- `operator`: viewer + restart_service, run_remediation
- `admin`: operator + manage_users, manage_platforms, manage_keys

### 3. Platform Management (`app/platforms.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `list_platforms()` | None | `List[Platform]` | Get all configured platforms |
| `add_platform(config)` | `PlatformConfig` | `Platform` | Add new platform connection |
| `update_platform(id, config)` | `str, PlatformConfig` | `Platform` | Update platform config |
| `delete_platform(id)` | `str` | `bool` | Remove platform and credentials |
| `test_connection(id)` | `str` | `ConnectionResult` | Test platform connectivity |
| `encrypt_credentials(creds)` | `Dict` | `str` | Encrypt credentials for storage |
| `decrypt_credentials(encrypted)` | `str` | `Dict` | Decrypt credentials at runtime |

**Supported Platforms:**
- AWS (access_key, secret_key, region)
- GCP (service_account_json, project_id)
- Azure (tenant_id, client_id, client_secret, subscription_id)
- Custom (api_endpoint, api_key)

### 4. API Key Management (`app/api_keys.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `list_keys()` | None | `List[ApiKeyInfo]` | Get keys with masked values |
| `add_key(name, value, service)` | `str, str, str` | `ApiKey` | Add and encrypt new key |
| `update_key(id, value)` | `str, str` | `ApiKey` | Update existing key |
| `delete_key(id)` | `str` | `bool` | Remove key |
| `get_key(service)` | `str` | `Optional[str]` | Get decrypted key for service |
| `mask_key(value)` | `str` | `str` | Return masked version (****xxxx) |

### 5. Settings UI (`app/settings_ui.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `render_settings(user)` | `User` | `gr.Blocks` | Render settings panel |
| `render_profile_tab(user)` | `User` | `gr.Tab` | User profile settings |
| `render_platforms_tab()` | None | `gr.Tab` | Platform management (admin) |
| `render_keys_tab()` | None | `gr.Tab` | API key management (admin) |

## Data Models

### User
```python
class User(BaseModel):
    id: str
    username: str
    password_hash: str
    role: str  # "viewer", "operator", "admin"
    email: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
```

### Session
```python
class Session(BaseModel):
    token: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    is_active: bool
```

### Platform
```python
class Platform(BaseModel):
    id: str
    name: str
    type: str  # "aws", "gcp", "azure", "custom"
    encrypted_credentials: str
    is_active: bool
    last_tested: Optional[datetime]
    connection_status: str  # "connected", "failed", "unknown"
    created_at: datetime
```

### ApiKey
```python
class ApiKey(BaseModel):
    id: str
    name: str
    service: str  # "sambanova", "modal", "hyperbolic", etc.
    encrypted_value: str
    created_at: datetime
    last_used: Optional[datetime]
```

### ApiKeyInfo (for display)
```python
class ApiKeyInfo(BaseModel):
    id: str
    name: str
    service: str
    masked_value: str  # "****xxxx"
    created_at: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Password Hash Irreversibility
*For any* password string, hashing it should produce a value that cannot be reversed to obtain the original password, and the same password should verify against its hash.
**Validates: Requirements 1.2**

### Property 2: Invalid Credentials Generic Error
*For any* invalid login attempt (wrong username, wrong password, or both), the error message should be identical and not reveal which field was incorrect.
**Validates: Requirements 1.3**

### Property 3: Session Logout Invalidation
*For any* valid session, after logout the session token should no longer validate.
**Validates: Requirements 1.4**

### Property 4: Role Permission Hierarchy
*For any* user with role R, they should have all permissions of roles below them in the hierarchy (admin > operator > viewer).
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 5: Non-Admin Access Denial
*For any* user without admin role attempting admin actions, the system should deny access.
**Validates: Requirements 2.4**

### Property 6: Credential Encryption
*For any* platform credentials saved, the stored value should be encrypted and not contain the plaintext credentials.
**Validates: Requirements 3.3**

### Property 7: Platform Deletion Cleanup
*For any* deleted platform, querying for that platform should return None and associated credentials should be removed.
**Validates: Requirements 3.5**

### Property 8: API Key Masking
*For any* API key displayed to users, only the last 4 characters should be visible, with the rest masked.
**Validates: Requirements 4.1**

### Property 9: API Key Encryption Round-Trip
*For any* API key, encrypting then decrypting should return the original value.
**Validates: Requirements 4.2, 4.5**

### Property 10: Settings Tab Visibility
*For any* non-admin user, the Platforms and API Keys tabs should not be visible in settings.
**Validates: Requirements 5.2**

## Error Handling

### Authentication Errors
- Invalid credentials: Generic "Invalid username or password" message
- Expired session: Redirect to login with "Session expired" message
- Missing session: Redirect to login

### Permission Errors
- Unauthorized access: Return 403 with "Access denied" message
- Invalid role: Log error, treat as viewer (fail-safe)

### Platform Errors
- Connection test failure: Display specific error from platform
- Encryption failure: Log error, do not save credentials
- Missing credentials: Prompt user to re-enter

### API Key Errors
- Invalid key format: Display validation error
- Decryption failure: Log error, prompt to re-add key

## Testing Strategy

### Property-Based Testing Framework
The project will use **Hypothesis** (Python) for property-based testing.

Each property-based test MUST:
1. Be annotated with the property number and requirements reference
2. Run a minimum of 100 iterations
3. Use smart generators that constrain inputs to valid ranges

### Unit Tests
- Password hashing and verification
- Session creation and validation
- Role permission checks
- Credential encryption/decryption
- Key masking

### Test Organization
```
tests/
├── test_auth.py           # Authentication property tests
├── test_permissions.py    # Role/permission property tests
├── test_platforms.py      # Platform management property tests
├── test_api_keys.py       # API key property tests
└── test_settings_ui.py    # Settings UI tests
```

### Test Annotations
Each property-based test will include:
```python
# **Feature: auth-platform-management, Property 1: Password Hash Irreversibility**
# **Validates: Requirements 1.2**
@given(...)
def test_password_hash_irreversibility(...):
    ...
```

