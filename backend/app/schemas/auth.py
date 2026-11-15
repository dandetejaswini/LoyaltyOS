import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class LoyaltyAccountSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    tier_id: str
    current_balance: int
    lifetime_accrued: int
    lifetime_redeemed: int
    qualifying_spend: Decimal
    status: str


class CustomerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    email: str
    first_name: str
    last_name: str
    status: str
    loyalty_account: Optional[LoyaltyAccountSummary] = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    customer: Optional[CustomerSummary] = None
    created_at: datetime


class AuthSyncRequest(BaseModel):
    provider: str
    id_token: str


class AuthSyncResponse(BaseModel):
    user: UserProfileResponse
    message: str


class LinkIdentityRequest(BaseModel):
    link_token: str


class LinkIdentityResponse(BaseModel):
    user: UserProfileResponse
    linked_provider: str
    message: str
