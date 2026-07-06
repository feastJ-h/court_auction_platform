from __future__ import annotations

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.database.session import session_scope
from backend.config import get_settings
from backend.services.audit_logs import create_audit_log
from backend.services.auth import create_user, list_users, set_user_active, set_user_role
from backend.web.dependencies import LoginRedirect, RequireAdmin


def register_admin_user_routes(
    app: FastAPI,
    templates: Jinja2Templates,
    *,
    require_admin: RequireAdmin,
    login_redirect: LoginRedirect,
) -> None:
    @app.get("/admin/users")
    def admin_users_page(request: Request, error: str = Query("")):
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect("/admin/users")
            return templates.TemplateResponse(
                request,
                "admin/users.html",
                {
                    "current_user": current_user,
                    "settings": get_settings(),
                    "active_section": "admin",
                    "active_subsection": "users",
                    "active_category": "",
                    "page_title": "Admin users",
                    "breadcrumbs": [{"label": "Admin", "href": "/admin"}, {"label": "Users", "href": "/admin/users"}],
                    "review_mode": get_settings().review_mode,
                    "users": list_users(session),
                    "error": error,
                },
            )

    @app.post("/admin/users")
    def admin_create_user(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        display_name: str = Form(""),
        role: str = Form("user"),
    ) -> RedirectResponse:
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables admin mutations.")
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect("/admin/users")
            try:
                user = create_user(
                    session,
                    username=username,
                    password=password,
                    display_name=display_name,
                    role=role,
                )
                create_audit_log(
                    session,
                    current_user.id,
                    "ADMIN_USER_CREATED",
                    "user",
                    user.id,
                    "Admin created user",
                    {"role": role},
                )
            except ValueError as exc:
                return RedirectResponse(url=f"/admin/users?error={str(exc)}", status_code=303)
        return RedirectResponse(url="/admin/users", status_code=303)

    @app.post("/admin/users/{user_id}/active")
    def admin_set_user_active(request: Request, user_id: int, is_active: bool = Form(...)) -> RedirectResponse:
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables admin mutations.")
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect("/admin/users")
            if current_user.id == user_id and not is_active:
                return RedirectResponse(url="/admin/users?error=self_deactivate_blocked", status_code=303)
            try:
                user = set_user_active(session, user_id=user_id, is_active=is_active)
                create_audit_log(
                    session,
                    current_user.id,
                    "ADMIN_USER_ACTIVE_CHANGED",
                    "user",
                    user.id,
                    "Admin changed user active state",
                    {"is_active": is_active},
                )
            except ValueError as exc:
                return RedirectResponse(url=f"/admin/users?error={str(exc)}", status_code=303)
        return RedirectResponse(url="/admin/users", status_code=303)

    @app.post("/admin/users/{user_id}/role")
    def admin_set_user_role(request: Request, user_id: int, role: str = Form(...)) -> RedirectResponse:
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables admin mutations.")
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect("/admin/users")
            try:
                user = set_user_role(session, user_id=user_id, role=role)
                create_audit_log(
                    session,
                    current_user.id,
                    "ADMIN_USER_ROLE_CHANGED",
                    "user",
                    user.id,
                    "Admin changed user role",
                    {"role": role},
                )
            except ValueError as exc:
                return RedirectResponse(url=f"/admin/users?error={str(exc)}", status_code=303)
        return RedirectResponse(url="/admin/users", status_code=303)
