from pydantic import BaseModel, HttpUrl, EmailStr
from typing import List, Literal, Optional, Dict, Any, Union


class Verification(BaseModel):
    status: str
    strategy: str


class EmailAddress(BaseModel):
    email_address: EmailStr
    id: str
    linked_to: List[Any]
    object: str
    verification: Verification


class HttpRequest(BaseModel):
    client_ip: str
    user_agent: str


class EventAttributes(BaseModel):
    http_request: HttpRequest


class UserData(BaseModel):
    birthday: Optional[Union[str, None]] = None
    created_at: Optional[int] = None
    email_addresses: Optional[List[EmailAddress]] = None
    external_accounts: Optional[List[Any]] = None
    external_id: Optional[str] = None
    first_name: Optional[str] = None
    gender: Optional[Union[str, None]] = None
    id: str
    image_url: Optional[HttpUrl] = None
    last_name: Optional[str] = None
    last_sign_in_at: Optional[int] = None
    object: Optional[str] = None
    password_enabled: Optional[bool] = None
    phone_numbers: Optional[List[Any]] = None
    primary_email_address_id: Optional[str] = None
    primary_phone_number_id: Optional[str] = None
    primary_web3_wallet_id: Optional[str] = None
    private_metadata: Optional[Dict[str, Any]] = None
    profile_image_url: Optional[HttpUrl] = None
    public_metadata: Optional[Dict[str, Any]] = None
    two_factor_enabled: Optional[bool] = None
    unsafe_metadata: Optional[Dict[str, Any]] = None
    updated_at: Optional[int] = None
    username: Optional[str] = None
    web3_wallets: Optional[List[Any]] = None


class ClerkWebhookEvent(BaseModel):
    data: UserData
    event_attributes: EventAttributes
    object: str
    timestamp: int
    type: Literal["user.created", "user.updated", "user.deleted"]
