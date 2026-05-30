from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(180), unique=True, index=True, nullable=False)
    password_hash = Column(String(220), nullable=True)
    role = Column(String(40), default="agent", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assigned_tickets = relationship(
        "Ticket",
        back_populates="assignee",
        foreign_keys="Ticket.assigned_to_id",
    )
    requested_tickets = relationship(
        "Ticket",
        back_populates="requester",
        foreign_keys="Ticket.requester_id",
    )
    comments = relationship("TicketComment", back_populates="author")
    attachments = relationship("TicketAttachment", back_populates="uploader")
    ticket_events = relationship("TicketEvent", back_populates="actor")
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    customer_graphs = relationship(
        "ClientGraph",
        back_populates="customer",
        foreign_keys="ClientGraph.customer_id",
    )
    assigned_graphs = relationship(
        "ClientGraph",
        back_populates="assigned_by",
        foreign_keys="ClientGraph.assigned_by_id",
    )
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    @property
    def photo_url(self):
        return self.profile.photo_url if self.profile else None

    @property
    def company(self):
        return self.profile.company if self.profile else None


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="password_reset_tokens")


class ClientGraph(Base):
    __tablename__ = "client_graphs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(180), nullable=False)
    description = Column(Text, nullable=True)
    graph_type = Column(String(40), default="network", nullable=False)
    chart_data = Column(Text, nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = relationship(
        "User",
        back_populates="customer_graphs",
        foreign_keys=[customer_id],
    )
    assigned_by = relationship(
        "User",
        back_populates="assigned_graphs",
        foreign_keys=[assigned_by_id],
    )


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(180), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(40), default="open", index=True, nullable=False)
    priority = Column(String(40), default="medium", index=True, nullable=False)
    category = Column(String(80), default="general", index=True, nullable=False)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_rating = Column(Integer, nullable=True)
    customer_rating_comment = Column(Text, nullable=True)
    customer_rated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    requester = relationship(
        "User",
        back_populates="requested_tickets",
        foreign_keys=[requester_id],
    )
    assignee = relationship(
        "User",
        back_populates="assigned_tickets",
        foreign_keys=[assigned_to_id],
    )
    comments = relationship(
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketComment.created_at",
    )
    attachments = relationship(
        "TicketAttachment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketAttachment.created_at",
    )
    events = relationship(
        "TicketEvent",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketEvent.created_at",
    )


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User", back_populates="comments")
    attachments = relationship(
        "TicketAttachment",
        back_populates="comment",
        cascade="all, delete-orphan",
        order_by="TicketAttachment.created_at",
    )


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    comment_id = Column(Integer, ForeignKey("ticket_comments.id"), nullable=True, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    content_type = Column(String(120), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    url = Column(String(320), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="attachments")
    comment = relationship("TicketComment", back_populates="attachments")
    uploader = relationship("User", back_populates="attachments")


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(60), nullable=False, index=True)
    message = Column(Text, nullable=False)
    field_name = Column(String(80), nullable=True)
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="events")
    actor = relationship("User", back_populates="ticket_events")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Identidad
    photo_url = Column(String(500), nullable=True)
    company = Column(String(180), nullable=True)
    phone = Column(String(20), nullable=True)
    job_title = Column(String(120), nullable=True)

    # Departamento
    department = Column(String(120), nullable=True)

    # Contacto - normalmente el email está en User, pero se pueden agregar contactos adicionales

    # Permisos - almacenados como JSON
    permissions = Column(JSON, default=list, nullable=False)

    # Canales - almacenados como JSON
    channels = Column(JSON, default=list, nullable=False)

    # Localización
    language = Column(String(10), default="es", nullable=False)  # ej: "es", "en", "fr"
    timezone = Column(String(50), default="America/Bogota", nullable=False)

    # Personalización de trabajo - almacenado como JSON
    work_preferences = Column(JSON, default=dict, nullable=False)

    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="profile")
