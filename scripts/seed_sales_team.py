import uuid
from database import SessionLocal
from models.user import User, UserRole
from models.employee import EmployeeProfile, Team, TeamMembership
from models.enquiry import LoanEnquiry

def seed_sales_team():
    with SessionLocal() as db:
        mgr = db.query(User).filter(User.email == "manager_test@credence.in").first()
        exec_user = db.query(User).filter(User.email == "exec_test@credence.in").first()

        if not mgr or not exec_user:
            print("Manager or Exec user not found. Ensure test users exist.")
            return

        # 1. Manager Profile
        if not mgr.employee_profile:
            mgr_profile = EmployeeProfile(
                user_id=mgr.id,
                employee_code="EMP-MGR-001",
                designation="Sales & Underwriting Manager",
                department="Retail Lending"
            )
            db.add(mgr_profile)
            print(f"Created EmployeeProfile for Manager: {mgr.name}")

        # 2. Executive Profile
        if not exec_user.employee_profile:
            exec_profile = EmployeeProfile(
                user_id=exec_user.id,
                employee_code="EMP-SPE-001",
                designation="Senior Loan Specialist",
                department="Retail Lending"
            )
            db.add(exec_profile)
            print(f"Created EmployeeProfile for Executive: {exec_user.name}")

        db.flush()

        # 3. Team
        team = db.query(Team).filter(Team.name == "Retail Lending Desk").first()
        if not team:
            team = Team(
                id=f"tm_{uuid.uuid4().hex[:12]}",
                name="Retail Lending Desk",
                description="Primary retail loan processing and partner bank coordination team",
                manager_user_id=mgr.id,
                is_active=True
            )
            db.add(team)
            db.flush()
            print(f"Created Team: {team.name} (Manager: {mgr.name})")

        # 4. Memberships
        # Manager membership
        mgr_mem = db.query(TeamMembership).filter(
            TeamMembership.team_id == team.id,
            TeamMembership.employee_user_id == mgr.id
        ).first()
        if not mgr_mem:
            mgr_mem = TeamMembership(
                id=f"tmem_{uuid.uuid4().hex[:12]}",
                team_id=team.id,
                employee_user_id=mgr.id,
                is_active=True
            )
            db.add(mgr_mem)

        # Executive membership
        exec_mem = db.query(TeamMembership).filter(
            TeamMembership.team_id == team.id,
            TeamMembership.employee_user_id == exec_user.id
        ).first()
        if not exec_mem:
            exec_mem = TeamMembership(
                id=f"tmem_{uuid.uuid4().hex[:12]}",
                team_id=team.id,
                employee_user_id=exec_user.id,
                is_active=True
            )
            db.add(exec_mem)
            print(f"Added {exec_user.name} to Team {team.name}")

        # 5. Link existing leads to this team if unassigned to a team
        for enq in db.query(LoanEnquiry).all():
            if not enq.assigned_team_id:
                enq.assigned_team_id = team.id

        db.commit()
        print("✓ Sales team hierarchy and lead team associations successfully synchronized!")

if __name__ == "__main__":
    seed_sales_team()

