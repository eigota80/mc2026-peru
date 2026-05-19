from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


VALID_STATUSES = {"open", "in_progress", "waiting_customer", "resolved", "escalated", "closed"}
VALID_PRIORITIES = {"low", "medium", "high", "urgent"}
VALID_ROLES = {"admin", "agent", "customer"}
VALID_GRAPH_TYPES = {"network", "bar", "line", "pie", "cacti"}


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    role: str = "agent"


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    role: Optional[str] = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=20, max_length=220)
    password: str = Field(..., min_length=8, max_length=128)


class MessageResponse(BaseModel):
    message: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ClientGraphBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=180)
    description: Optional[str] = Field(default=None, max_length=600)
    graph_type: str = "network"
    chart_data: str = Field(..., min_length=2, max_length=4000)
    customer_id: int


class ClientGraphCreate(ClientGraphBase):
    pass


class ClientGraphUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=180)
    description: Optional[str] = Field(default=None, max_length=600)
    graph_type: Optional[str] = None
    chart_data: Optional[str] = Field(default=None, min_length=2, max_length=4000)
    customer_id: Optional[int] = None


class ClientGraphRead(ClientGraphBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assigned_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    customer: Optional[UserRead] = None
    assigned_by: Optional[UserRead] = None


class TicketCommentBase(BaseModel):
    body: str = Field(..., min_length=2)
    author_id: Optional[int] = None


class TicketCommentCreate(TicketCommentBase):
    pass


class TicketCommentRead(TicketCommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    created_at: datetime
    author: Optional[UserRead] = None


class TicketAttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    uploaded_by_id: Optional[int] = None
    original_filename: str
    content_type: str
    size_bytes: int
    url: str
    created_at: datetime
    uploader: Optional[UserRead] = None


class TicketEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    actor_id: Optional[int] = None
    event_type: str
    message: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime
    actor: Optional[UserRead] = None


class TicketBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=180)
    description: str = Field(..., min_length=5)
    priority: str = "medium"
    category: str = Field(default="general", max_length=80)
    requester_id: Optional[int] = None
    assigned_to_id: Optional[int] = None


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=180)
    description: Optional[str] = Field(default=None, min_length=5)
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=80)
    requester_id: Optional[int] = None
    assigned_to_id: Optional[int] = None


class TicketRead(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    requester: Optional[UserRead] = None
    assignee: Optional[UserRead] = None
    comments: List[TicketCommentRead] = []
    attachments: List[TicketAttachmentRead] = []
    events: List[TicketEventRead] = []


class TicketStatistics(BaseModel):
    total: int
    by_status: dict
    by_priority: dict
    by_category: dict
    by_assignee: dict
