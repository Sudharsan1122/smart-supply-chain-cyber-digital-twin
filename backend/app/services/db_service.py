"""Database Facade wrapping SQLAlchemy queries and seeding the 10-node supply chain network."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, PartnerOrganization, SupplyEdge, SupplyNode, User
from app.schemas import SupplyEdgeCreate, SupplyNodeCreate, UserCreate
from app.security import RoleEnum, hash_password

SEED_NODES: list[dict[str, object]] = [
    {"node_code": "SUP-001", "name": "Chennai Tier-1 Chip Supplier", "node_type": "SUPPLIER", "region": "SOUTH", "capacity": 1200.0, "fixed_cost": 2500.0, "inventory": 950.0, "demand": 320.0, "org_id": "101"},
    {"node_code": "SUP-002", "name": "Pune Precision Components", "node_type": "SUPPLIER", "region": "SOUTH", "capacity": 1100.0, "fixed_cost": 2200.0, "inventory": 880.0, "demand": 280.0, "org_id": "102"},
    {"node_code": "FAC-001", "name": "Bengaluru Assembly Plant", "node_type": "FACTORY", "region": "SOUTH", "capacity": 1500.0, "fixed_cost": 6000.0, "inventory": 700.0, "demand": 420.0, "org_id": "103"},
    {"node_code": "FAC-002", "name": "Hyderabad Electronics Factory", "node_type": "FACTORY", "region": "SOUTH", "capacity": 1300.0, "fixed_cost": 5500.0, "inventory": 640.0, "demand": 390.0, "org_id": "104"},
    {"node_code": "PRT-001", "name": "Mumbai JNPT Maritime Port", "node_type": "PORT", "region": "SOUTH", "capacity": 2000.0, "fixed_cost": 4000.0, "inventory": 1100.0, "demand": 310.0, "org_id": "105"},
    {"node_code": "WH-001", "name": "Delhi NCR Central Hub", "node_type": "WAREHOUSE", "region": "NORTH", "capacity": 1400.0, "fixed_cost": 3500.0, "inventory": 820.0, "demand": 260.0, "org_id": None},
    {"node_code": "WH-002", "name": "Kolkata Eastern DC", "node_type": "WAREHOUSE", "region": "EAST", "capacity": 1000.0, "fixed_cost": 3000.0, "inventory": 540.0, "demand": 210.0, "org_id": None},
    {"node_code": "WH-003", "name": "Ahmedabad Western Hub", "node_type": "WAREHOUSE", "region": "WEST", "capacity": 1150.0, "fixed_cost": 3200.0, "inventory": 610.0, "demand": 190.0, "org_id": None},
    {"node_code": "RET-001", "name": "North India Retail Cluster", "node_type": "RETAILER", "region": "NORTH", "capacity": 900.0, "fixed_cost": 1500.0, "inventory": 300.0, "demand": 420.0, "org_id": None},
    {"node_code": "RET-002", "name": "South India Retail Cluster", "node_type": "RETAILER", "region": "SOUTH", "capacity": 950.0, "fixed_cost": 1500.0, "inventory": 340.0, "demand": 450.0, "org_id": "101"},
]

SEED_EDGES: list[dict[str, object]] = [
    {"edge_code": "LANE-01", "source_node_code": "SUP-001", "target_node_code": "FAC-001", "lead_time_days": 2.0, "unit_cost": 3.2, "max_flow": 900.0},
    {"edge_code": "LANE-02", "source_node_code": "SUP-002", "target_node_code": "FAC-002", "lead_time_days": 2.5, "unit_cost": 3.5, "max_flow": 850.0},
    {"edge_code": "LANE-03", "source_node_code": "FAC-001", "target_node_code": "PRT-001", "lead_time_days": 3.0, "unit_cost": 4.0, "max_flow": 1000.0},
    {"edge_code": "LANE-04", "source_node_code": "FAC-002", "target_node_code": "WH-001", "lead_time_days": 3.5, "unit_cost": 4.8, "max_flow": 950.0},
    {"edge_code": "LANE-05", "source_node_code": "PRT-001", "target_node_code": "WH-002", "lead_time_days": 4.0, "unit_cost": 5.1, "max_flow": 900.0},
    {"edge_code": "LANE-06", "source_node_code": "PRT-001", "target_node_code": "WH-003", "lead_time_days": 2.0, "unit_cost": 3.8, "max_flow": 850.0},
    {"edge_code": "LANE-07", "source_node_code": "WH-001", "target_node_code": "RET-001", "lead_time_days": 1.5, "unit_cost": 2.9, "max_flow": 700.0},
    {"edge_code": "LANE-08", "source_node_code": "WH-002", "target_node_code": "RET-001", "lead_time_days": 2.5, "unit_cost": 3.4, "max_flow": 600.0},
    {"edge_code": "LANE-09", "source_node_code": "WH-003", "target_node_code": "RET-002", "lead_time_days": 2.0, "unit_cost": 3.1, "max_flow": 750.0},
    {"edge_code": "LANE-10", "source_node_code": "FAC-001", "target_node_code": "RET-002", "lead_time_days": 1.0, "unit_cost": 2.5, "max_flow": 650.0},
]

SEED_PARTNER_ORGS: list[dict[str, object]] = [
    {"org_id": 101, "name": "Apex Semiconductor South", "region": "SOUTH", "is_active": True},
    {"org_id": 102, "name": "Bharat Precision Systems", "region": "SOUTH", "is_active": True},
    {"org_id": 103, "name": "Deccan Logistics & Foundry", "region": "SOUTH", "is_active": True},
    {"org_id": 104, "name": "Kaveri Microelectronics", "region": "SOUTH", "is_active": True},
    {"org_id": 105, "name": "Coromandel Industrial Supply", "region": "SOUTH", "is_active": True},
]


class DbServiceFacade:
    """Facade encapsulating SQLAlchemy persistence operations for routers and domain services."""

    def get_user_by_username(self, db: Session, username: str) -> User | None:
        """Fetch a user by username."""
        return db.execute(select(User).where(User.username == username)).scalar_one_or_none()

    def create_user(self, db: Session, payload: UserCreate) -> User:
        """Create and persist a new user with bcrypt-hashed password."""
        user = User(
            username=payload.username,
            hashed_password=hash_password(payload.password),
            role=payload.role.value,
            org_id=payload.org_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def list_nodes(self, db: Session) -> list[SupplyNode]:
        """Return all supply chain nodes ordered by code."""
        return list(db.execute(select(SupplyNode).order_by(SupplyNode.node_code.asc())).scalars().all())

    def get_node_by_code(self, db: Session, node_code: str) -> SupplyNode | None:
        """Fetch a single SupplyNode by its unique code."""
        return db.execute(select(SupplyNode).where(SupplyNode.node_code == node_code)).scalar_one_or_none()

    def upsert_node(self, db: Session, payload: SupplyNodeCreate) -> SupplyNode:
        """Create or update a supply chain node."""
        node = self.get_node_by_code(db, payload.node_code)
        if node is None:
            node = SupplyNode(**payload.model_dump())
            db.add(node)
        else:
            for key, val in payload.model_dump().items():
                setattr(node, key, val)
        db.commit()
        db.refresh(node)
        return node

    def list_edges(self, db: Session) -> list[SupplyEdge]:
        """Return all supply chain edges ordered by code."""
        return list(db.execute(select(SupplyEdge).order_by(SupplyEdge.edge_code.asc())).scalars().all())

    def upsert_edge(self, db: Session, payload: SupplyEdgeCreate) -> SupplyEdge:
        """Create or update a supply chain transportation lane."""
        edge = db.execute(select(SupplyEdge).where(SupplyEdge.edge_code == payload.edge_code)).scalar_one_or_none()
        if edge is None:
            edge = SupplyEdge(**payload.model_dump())
            db.add(edge)
        else:
            for key, val in payload.model_dump().items():
                setattr(edge, key, val)
        db.commit()
        db.refresh(edge)
        return edge

    def list_audit_logs(self, db: Session, limit: int = 100) -> list[AuditLog]:
        """Return recent audit logs ordered newest first."""
        return list(db.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).scalars().all())

    def seed_initial_data(self, db: Session) -> None:
        """Seed the 10-node supply chain network, 5 partner orgs, and RBAC demo users if empty."""
        if self.list_nodes(db):
            return
        for n_data in SEED_NODES:
            db.add(SupplyNode(**n_data))
        for e_data in SEED_EDGES:
            db.add(SupplyEdge(**e_data))
        for p_data in SEED_PARTNER_ORGS:
            db.add(PartnerOrganization(**p_data))
        default_users = [
            ("admin_user", RoleEnum.ADMIN.value, None),
            ("planner_user", RoleEnum.PLANNER.value, None),
            ("viewer_user", RoleEnum.VIEWER.value, None),
            ("partner_user", RoleEnum.PARTNER.value, "101"),
            ("partner_other", RoleEnum.PARTNER.value, "102"),
        ]
        for uname, role_val, org_val in default_users:
            if not self.get_user_by_username(db, uname):
                db.add(
                    User(
                        username=uname,
                        hashed_password=hash_password(f"Scdt#{uname}2026!"),
                        role=role_val,
                        org_id=org_val,
                        region="SOUTH",
                    )
                )
        db.commit()


db_service = DbServiceFacade()
