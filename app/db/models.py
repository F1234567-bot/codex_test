from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(200))
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), default="general")
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[str] = mapped_column(String(20), default="Moyen")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Briefing(Base):
    __tablename__ = "briefings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date_key: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    executive_summary: Mapped[str] = mapped_column(Text)
    opportunity_radar: Mapped[str] = mapped_column(Text)
    critical_alerts: Mapped[str] = mapped_column(Text)
    recommendations: Mapped[str] = mapped_column(Text)
    used_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    actions: Mapped[list["ActionItem"]] = relationship(back_populates="briefing", cascade="all, delete")


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    briefing_id: Mapped[int] = mapped_column(ForeignKey("briefings.id"))
    title: Mapped[str] = mapped_column(String(300))
    owner: Mapped[str] = mapped_column(String(150), default="À assigner")
    status: Mapped[str] = mapped_column(String(50), default="todo")
    due_date: Mapped[str] = mapped_column(String(30), default="aujourd'hui")

    briefing: Mapped[Briefing] = relationship(back_populates="actions")


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), unique=True)
    api_key: Mapped[str] = mapped_column(String(300), default="")
    model_name: Mapped[str] = mapped_column(String(150), default="")
    base_url: Mapped[str] = mapped_column(String(250), default="")
    role: Mapped[str] = mapped_column(String(50), default="available")
