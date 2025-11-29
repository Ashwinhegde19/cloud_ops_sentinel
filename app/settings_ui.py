"""
Settings UI module for Cloud Ops Sentinel
Tabbed settings interface for profile, platforms, and API keys.
"""

import gradio as gr
from typing import Optional, Tuple
from datetime import datetime

from .models import User
from .auth import update_user_password, get_user_by_id
from .permissions import is_admin, can_manage_platforms, can_manage_api_keys
from .platforms import (
    list_platforms, add_platform, delete_platform, test_connection,
    get_platform_types, PLATFORM_TYPES
)
from .api_keys import (
    list_keys, add_key, delete_key, get_supported_services
)
from .models import PlatformConfig


def render_profile_tab(user: User) -> str:
    """Render profile settings HTML."""
    return f"""
<div style="padding: 20px;">
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
        <h3 style="color: #e2e8f0; margin: 0 0 20px 0;">👤 Profile Information</h3>
        <div style="display: grid; gap: 16px;">
            <div>
                <label style="color: #94a3b8; font-size: 12px; text-transform: uppercase;">Username</label>
                <div style="color: #e2e8f0; font-size: 16px; font-weight: 500;">{user.username}</div>
            </div>
            <div>
                <label style="color: #94a3b8; font-size: 12px; text-transform: uppercase;">Role</label>
                <div style="color: #6366f1; font-size: 16px; font-weight: 500; text-transform: capitalize;">{user.role}</div>
            </div>
            <div>
                <label style="color: #94a3b8; font-size: 12px; text-transform: uppercase;">Email</label>
                <div style="color: #e2e8f0; font-size: 16px;">{user.email or 'Not set'}</div>
            </div>
            <div>
                <label style="color: #94a3b8; font-size: 12px; text-transform: uppercase;">Member Since</label>
                <div style="color: #e2e8f0; font-size: 16px;">{user.created_at.strftime('%Y-%m-%d')}</div>
            </div>
            <div>
                <label style="color: #94a3b8; font-size: 12px; text-transform: uppercase;">Last Login</label>
                <div style="color: #e2e8f0; font-size: 16px;">{user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'}</div>
            </div>
        </div>
    </div>
</div>
"""


def render_platforms_list() -> str:
    """Render platforms list HTML."""
    platforms = list_platforms()
    
    if not platforms:
        return """
<div style="text-align: center; padding: 40px;">
    <div style="font-size: 48px; margin-bottom: 16px;">🌐</div>
    <p style="color: #94a3b8;">No platforms configured yet.</p>
    <p style="color: #64748b; font-size: 12px;">Add a cloud platform to start monitoring.</p>
</div>
"""
    
    html = '<div style="display: grid; gap: 16px;">'
    
    for p in platforms:
        status_color = "#10b981" if p.connection_status == "connected" else "#ef4444" if p.connection_status == "failed" else "#f59e0b"
        status_icon = "✅" if p.connection_status == "connected" else "❌" if p.connection_status == "failed" else "❓"
        
        type_icons = {"aws": "☁️", "gcp": "🔷", "azure": "🔶", "custom": "⚙️"}
        type_icon = type_icons.get(p.type, "🌐")
        
        html += f"""
<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px; padding: 16px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 24px;">{type_icon}</span>
            <div>
                <div style="color: #e2e8f0; font-weight: 600;">{p.name}</div>
                <div style="color: #64748b; font-size: 12px; text-transform: uppercase;">{p.type}</div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: {status_color};">{status_icon} {p.connection_status}</span>
        </div>
    </div>
</div>
"""
    
    html += '</div>'
    return html


def render_api_keys_list() -> str:
    """Render API keys list HTML."""
    keys = list_keys()
    
    if not keys:
        return """
<div style="text-align: center; padding: 40px;">
    <div style="font-size: 48px; margin-bottom: 16px;">🔑</div>
    <p style="color: #94a3b8;">No API keys configured yet.</p>
    <p style="color: #64748b; font-size: 12px;">Add API keys for sponsor integrations.</p>
</div>
"""
    
    html = '<div style="display: grid; gap: 12px;">'
    
    service_icons = {
        "sambanova": "🧠", "modal": "🚀", "hyperbolic": "🔮",
        "blaxel": "⚡", "huggingface": "🤗", "openai": "🤖", "anthropic": "🔷"
    }
    
    for k in keys:
        icon = service_icons.get(k.service, "🔑")
        
        html += f"""
<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px; padding: 16px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 20px;">{icon}</span>
            <div>
                <div style="color: #e2e8f0; font-weight: 500;">{k.name}</div>
                <div style="color: #64748b; font-size: 12px; text-transform: uppercase;">{k.service}</div>
            </div>
        </div>
        <div style="font-family: monospace; color: #94a3b8; background: rgba(99, 102, 241, 0.1); padding: 4px 12px; border-radius: 6px;">
            {k.masked_value}
        </div>
    </div>
</div>
"""
    
    html += '</div>'
    return html


def change_password(user_id: str, current_pwd: str, new_pwd: str, confirm_pwd: str) -> str:
    """Handle password change."""
    from .auth import authenticate, get_user_by_id
    
    user = get_user_by_id(user_id)
    if not user:
        return "❌ User not found"
    
    # Verify current password
    from .auth import verify_password
    if not verify_password(current_pwd, user.password_hash):
        return "❌ Current password is incorrect"
    
    # Check new password match
    if new_pwd != confirm_pwd:
        return "❌ New passwords do not match"
    
    # Check password length
    if len(new_pwd) < 6:
        return "❌ Password must be at least 6 characters"
    
    # Update password
    if update_user_password(user_id, new_pwd):
        return "✅ Password changed successfully"
    else:
        return "❌ Failed to update password"


def add_new_platform(name: str, platform_type: str, creds_json: str) -> Tuple[str, str]:
    """Add a new platform."""
    import json
    
    if not name or not platform_type:
        return "❌ Name and type are required", render_platforms_list()
    
    try:
        credentials = json.loads(creds_json) if creds_json else {}
    except json.JSONDecodeError:
        return "❌ Invalid JSON for credentials", render_platforms_list()
    
    # Validate required fields
    required = PLATFORM_TYPES.get(platform_type, {}).get("required", [])
    missing = [f for f in required if not credentials.get(f)]
    if missing:
        return f"❌ Missing required fields: {', '.join(missing)}", render_platforms_list()
    
    config = PlatformConfig(name=name, type=platform_type, credentials=credentials)
    platform = add_platform(config)
    
    return f"✅ Platform '{name}' added successfully", render_platforms_list()


def add_new_api_key(name: str, service: str, value: str) -> Tuple[str, str]:
    """Add a new API key."""
    if not name or not service or not value:
        return "❌ All fields are required", render_api_keys_list()
    
    add_key(name, value, service)
    return f"✅ API key '{name}' added successfully", render_api_keys_list()


def create_settings_tab(user: User):
    """Create the settings tab content based on user role."""
    with gr.Tab("⚙️ Settings", id="settings"):
        gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 16px 0;">Settings</h2>')
        
        with gr.Tabs():
            # Profile tab (all users)
            with gr.Tab("👤 Profile"):
                profile_html = gr.HTML(value=render_profile_tab(user))
                
                gr.HTML('<h4 style="color: #e2e8f0; margin: 20px 0 12px 0;">Change Password</h4>')
                with gr.Row():
                    current_pwd = gr.Textbox(label="Current Password", type="password", scale=1)
                    new_pwd = gr.Textbox(label="New Password", type="password", scale=1)
                    confirm_pwd = gr.Textbox(label="Confirm New Password", type="password", scale=1)
                
                change_pwd_btn = gr.Button("🔒 Change Password", variant="primary")
                pwd_result = gr.HTML()
                
                change_pwd_btn.click(
                    fn=lambda c, n, cf: change_password(user.id, c, n, cf),
                    inputs=[current_pwd, new_pwd, confirm_pwd],
                    outputs=[pwd_result]
                )
            
            # Platforms tab (admin only)
            if is_admin(user):
                with gr.Tab("🌐 Platforms"):
                    platforms_list = gr.HTML(value=render_platforms_list())
                    
                    gr.HTML('<h4 style="color: #e2e8f0; margin: 20px 0 12px 0;">Add New Platform</h4>')
                    with gr.Row():
                        platform_name = gr.Textbox(label="Platform Name", placeholder="My AWS Account")
                        platform_type = gr.Dropdown(
                            label="Platform Type",
                            choices=["aws", "gcp", "azure", "custom"],
                            value="aws"
                        )
                    
                    platform_creds = gr.Textbox(
                        label="Credentials (JSON)",
                        placeholder='{"access_key": "...", "secret_key": "...", "region": "us-east-1"}',
                        lines=3
                    )
                    
                    add_platform_btn = gr.Button("➕ Add Platform", variant="primary")
                    platform_result = gr.HTML()
                    
                    add_platform_btn.click(
                        fn=add_new_platform,
                        inputs=[platform_name, platform_type, platform_creds],
                        outputs=[platform_result, platforms_list]
                    )
            
            # API Keys tab (admin only)
            if is_admin(user):
                with gr.Tab("🔑 API Keys"):
                    keys_list = gr.HTML(value=render_api_keys_list())
                    
                    gr.HTML('<h4 style="color: #e2e8f0; margin: 20px 0 12px 0;">Add New API Key</h4>')
                    with gr.Row():
                        key_name = gr.Textbox(label="Key Name", placeholder="SambaNova Production")
                        key_service = gr.Dropdown(
                            label="Service",
                            choices=get_supported_services(),
                            value="sambanova"
                        )
                    
                    key_value = gr.Textbox(label="API Key Value", type="password", placeholder="sk-...")
                    
                    add_key_btn = gr.Button("➕ Add API Key", variant="primary")
                    key_result = gr.HTML()
                    
                    add_key_btn.click(
                        fn=add_new_api_key,
                        inputs=[key_name, key_service, key_value],
                        outputs=[key_result, keys_list]
                    )
