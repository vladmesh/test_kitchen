from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mini_crm.core.db import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")

    members: Mapped[list["OrganizationMember"]] = relationship("OrganizationMember", back_populates="organization")
    tags: Mapped[list["Tag"]] = relationship("Tag", back_populates="organization", cascade="all,delete-orphan")
