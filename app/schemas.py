from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer

# ---------- Auth ----------


class SignupIn(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str  # Enum ise string olarak serileştireceğiz
    model_config = ConfigDict(from_attributes=True)

    # Role bir Enum ise .value, değilse str(v) döndür
    @field_serializer("role")
    def _role_to_str(self, v):
        return getattr(v, "value", str(v))


# ---------- Nodes ----------
# INPUT modellerinde 'status' YOK -> durumu sadece backend değiştirir

class NodeBase(BaseModel):
    type: Optional[str] = "lead"
    title: str
    notes: Optional[str] = ""


class NodeCreate(NodeBase):
    pass


class NodeUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[str] = None


# OUTPUT: status ve summary burada görünür
class NodeOut(NodeBase):
    id: int
    status: str     # Enum ise string
    summary: str
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("status")
    def _status_to_str(self, v):
        return getattr(v, "value", str(v))


# ---------- Jobs ----------

class JobEnqueueOut(BaseModel):
    job_id: str


class JobStatusOut(BaseModel):
    job_id: str
    status: str
    result: Optional[str] = None
