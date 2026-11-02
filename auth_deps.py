from typing import Optional, List
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from database import get_db
import auth
from models.user import User, UserRole
from models.employee import Team, TeamMembership

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates the Bearer token and returns the authoritative User entity.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token."
        )

    token = authorization.split(" ")[1]
    claims = auth.decode_access_token(token)
    if not claims or not claims.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token."
        )

    user = auth.get_user_by_id(claims["sub"], db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this session no longer exists."
        )

    return user

def get_optional_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional user extractor for endpoints that serve both anonymous and authenticated users.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.split(" ")[1]
        claims = auth.decode_access_token(token)
        if claims and claims.get("sub"):
            return auth.get_user_by_id(claims["sub"], db=db)
    except Exception:
        pass
    return None

def require_roles(*allowed_roles: UserRole):
    """
    Enforces role-based access control.
    Matches current_user.role against the allowed roles enum.
    """
    def checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role
        if isinstance(user_role, str):
            try:
                user_role = UserRole(user_role)
            except ValueError:
                pass

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: role '{current_user.role}' is not authorized for this action."
            )
        return current_user

    return checker

def get_authorized_lead(
    lead_id: str,
    current_user: User,
    db: Session
):
    """
    Enforces object-level lead authorization:
    - SALES_ADMIN / SYSTEM_ADMIN: Full access company-wide
    - SALES_MANAGER: Access if lead is assigned to manager's team or lead is unassigned
    - SALES_EXECUTIVE: Access only if lead is assigned to this user
    - CUSTOMER: Access only if customer_user_id matches
    """
    from models.enquiry import LoanEnquiry
    lead = db.query(LoanEnquiry).filter(LoanEnquiry.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with id '{lead_id}' not found."
        )

    user_role = current_user.role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            pass

    if user_role in (UserRole.SALES_ADMIN, UserRole.SYSTEM_ADMIN):
        return lead

    if user_role == UserRole.SALES_MANAGER:
        manager_team_ids = set()
        if current_user.employee_profile and current_user.employee_profile.memberships:
            manager_team_ids = {m.team_id for m in current_user.employee_profile.memberships}
        
        teams_managed = db.query(Team.id).filter(Team.manager_user_id == current_user.id).all()
        for t in teams_managed:
            manager_team_ids.add(t[0])

        if manager_team_ids:
            team_exec_user_ids = db.query(TeamMembership.employee_user_id).filter(
                TeamMembership.team_id.in_(list(manager_team_ids))
            ).all()
            team_user_ids = {uid[0] for uid in team_exec_user_ids}
            team_user_ids.add(current_user.id)

            if (lead.assigned_team_id in manager_team_ids or 
                lead.assigned_to_user_id in team_user_ids or 
                not lead.assigned_to_user_id):
                return lead
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: this lead is not within your authorized team scope."
            )

        # When no restrictive team partition is configured, Sales Manager has department-wide scope
        return lead

    if user_role == UserRole.SALES_EXECUTIVE:
        if lead.assigned_to_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you can only access leads assigned directly to you."
            )
        return lead

    if user_role == UserRole.CUSTOMER:
        if lead.customer_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you can only view your own loan inquiries."
            )
        return lead

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied."
    )
