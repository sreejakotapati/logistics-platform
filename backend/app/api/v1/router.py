"""Aggregates all /api/v1 module routers."""
from fastapi import APIRouter

from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.organizations.router import router as organizations_router
from app.modules.rbac.router import router as rbac_router
from app.modules.security.router import router as security_router
from app.modules.tenancy.router import router as tenancy_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(tenancy_router)
api_router.include_router(organizations_router)
api_router.include_router(rbac_router)
api_router.include_router(audit_router)
api_router.include_router(security_router)
