from datetime import time
from typing import Optional

from sqlalchemy import Boolean, Column, Float, String, Time
from sqlmodel import Field, SQLModel


class AccidentDetail(SQLModel, table=True):
    __tablename__ = "accident_detail"

    Detail_id: Optional[int] = Field(default=None, primary_key=True)
    File_name: str = Field(sa_column=Column(String(30), nullable=False))
    TXT_File_path: Optional[str] = Field(default=None, sa_column=Column(String(30), nullable=True))
    Video_File_path: Optional[str] = Field(default=None, sa_column=Column(String(30), nullable=True))
    bbox_x1: Optional[float] = Field(default=None, sa_column=Column(Float, nullable=True))
    bbox_y1: Optional[float] = Field(default=None, sa_column=Column(Float, nullable=True))
    bbox_x2: Optional[float] = Field(default=None, sa_column=Column(Float, nullable=True))
    bbox_y2: Optional[float] = Field(default=None, sa_column=Column(Float, nullable=True))


class UserLogin(SQLModel, table=True):
    __tablename__ = "user_login"

    Login_id: int = Field(primary_key=True)
    User_id: int = Field(foreign_key="user.User_id", nullable=False)
    Login_id_str: str = Field(sa_column=Column(String(30), unique=True, nullable=False))
    Login_pw: str = Field(sa_column=Column(String(30), nullable=False))


class User(SQLModel, table=True):
    __tablename__ = "user"

    User_id: Optional[int] = Field(default=None, primary_key=True)
    User_name: Optional[str] = Field(default=None, sa_column=Column(String(10), nullable=True))
    User_role: Optional[str] = Field(default=None, sa_column=Column(String(10), nullable=True))
    active: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
    )
    Login_id: int = Field(foreign_key="user_login.Login_id", nullable=False)


class Device(SQLModel, table=True):
    __tablename__ = "device"

    Device_id: Optional[int] = Field(default=None, primary_key=True)
    Device_name: Optional[str] = Field(default=None, sa_column=Column(String(20), nullable=True))
    Target: int = Field(foreign_key="user.User_id", nullable=False)
    Server_url: Optional[str] = Field(default=None, sa_column=Column(String(20), nullable=True))
    active: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
    )


class Accident(SQLModel, table=True):
    __tablename__ = "accident"

    Accident_id: int = Field(primary_key=True)
    User_id: int = Field(foreign_key="user.User_id", nullable=False)
    Device_id: int = Field(foreign_key="device.Device_id", nullable=False)
    Type: Optional[str] = Field(default=None, sa_column=Column(String(30), nullable=True))
    Time: Optional[time] = Field(default=None, sa_column=Column(Time, nullable=True))
    Detail_id: int = Field(foreign_key="accident_detail.Detail_id", nullable=False)


class Matching(SQLModel, table=True):
    __tablename__ = "matching"

    Matching_id: Optional[int] = Field(default=None, primary_key=True)
    Gurdian: int = Field(foreign_key="user.User_id", nullable=False)
    Recipient: int = Field(foreign_key="user.User_id", nullable=False)
    active: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
    )
