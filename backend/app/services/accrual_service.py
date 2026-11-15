import math
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.models.loyalty import Customer, LoyaltyAccount, Order, OrderLine, Tier
from backend.app.models.ledger import PointsTransaction, PointsLot
from backend.app.schemas.loyalty import OrderCreateRequest, OrderAccrualResponse, OrderLineResponse
from backend.app.services.audit_service import AuditService
from backend.app.core.errors import NotFoundError, ConflictError, BadRequestError
from backend.app.core.logging import logger


class AccrualService:
    """
    Workflow B: Order Creation and Atomic Points Accrual.
    Enforces eligible net spend calculation, tier multiplier, financial floor-rounding,
    FIFO lot creation with 365-day expiry, and append-only ledger transaction.
    """

    @classmethod
    async def process_order_accrual(
        cls,
        db: AsyncSession,
        req: OrderCreateRequest,
        actor_id: str,
    ) -> OrderAccrualResponse:
        # 1. Check idempotency on PointsTransaction and Order ID
        tx_chk = select(PointsTransaction).where(PointsTransaction.idempotency_key == req.idempotency_key)
        tx_chk_res = await db.execute(tx_chk)
        if tx_chk_res.scalar_one_or_none():
            raise ConflictError(detail=f"Operation with idempotency key '{req.idempotency_key}' was already processed.")

        # 2. Retrieve Customer and Loyalty Account
        cust_stmt = select(Customer).options(selectinload(Customer.loyalty_account).selectinload(LoyaltyAccount.tier)).where(Customer.customer_id == req.customer_id)
        cust_res = await db.execute(cust_stmt)
        customer = cust_res.scalar_one_or_none()
        if not customer:
            await AuditService.log_rejection(
                db=db,
                actor_id=actor_id,
                operation_type="ORDER_ACCRUAL",
                error_code="CUSTOMER_NOT_FOUND",
                error_message=f"Customer '{req.customer_id}' does not exist.",
                payload={"customer_id": req.customer_id, "idempotency_key": req.idempotency_key}
            )
            await db.commit()
            raise NotFoundError(detail=f"Customer '{req.customer_id}' not found.")

        account = customer.loyalty_account
        if not account or account.status != "ACTIVE":
            await AuditService.log_rejection(
                db=db,
                actor_id=actor_id,
                operation_type="ORDER_ACCRUAL",
                error_code="ACCOUNT_INACTIVE",
                error_message=f"Loyalty account for customer '{req.customer_id}' is not in ACTIVE state.",
                account_id=account.account_id if account else None,
                payload={"customer_id": req.customer_id}
            )
            await db.commit()
            raise BadRequestError(detail="Loyalty account is not active.")

        tier = account.tier
        tier_multiplier = tier.earning_multiplier if tier else Decimal("1.00")

        # 3. Determine Order ID
        order_id = req.order_id or f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        ord_chk = select(Order).where(Order.order_id == order_id)
        ord_chk_res = await db.execute(ord_chk)
        if ord_chk_res.scalar_one_or_none():
            raise ConflictError(detail=f"Order '{order_id}' already exists in the system.")

        # 4. Process Order Lines & Compute Eligible Net Spend
        # Formula: Eligible Net Spend = SUM(quantity * unit_price - item_discount) for is_eligible=True
        order_lines: List[OrderLine] = []
        eligible_net_spend = Decimal("0.00")
        total_merchandise_gross = Decimal("0.00")

        now = datetime.now(timezone.utc)
        lot_expires_at = now + timedelta(days=365)

        for line_req in req.lines:
            line_gross = line_req.quantity * line_req.unit_price
            line_net = max(Decimal("0.00"), line_gross - line_req.item_discount)
            total_merchandise_gross += line_gross

            if line_req.is_eligible:
                eligible_net_spend += line_net

            order_line = OrderLine(
                order_line_id=f"ORDL-{order_id}-{line_req.line_number:02d}",
                order_id=order_id,
                line_number=line_req.line_number,
                sku=line_req.sku,
                product_name=line_req.product_name,
                category=line_req.category,
                quantity=line_req.quantity,
                unit_price=line_req.unit_price,
                item_discount=line_req.item_discount,
                net_amount=line_net,
                is_eligible=line_req.is_eligible,
                created_at=now,
            )
            order_lines.append(order_line)

        # Gross Order Amount includes merchandise, taxes, shipping, minus discounts
        gross_order_amount = max(Decimal("0.00"), total_merchandise_gross + req.tax_amount + req.shipping_amount - req.discount_amount)

        # 5. Apply Financial Floor-Rounding Rule (BR-02)
        # points = floor(eligible_net_spend * multiplier)
        calculated_points = float(eligible_net_spend * tier_multiplier)
        points_to_accrue = math.floor(calculated_points)

        # 6. Create Order record
        order = Order(
            order_id=order_id,
            customer_id=customer.customer_id,
            order_date=now,
            gross_amount=gross_order_amount,
            tax_amount=req.tax_amount,
            shipping_amount=req.shipping_amount,
            discount_amount=req.discount_amount,
            eligible_net_spend=eligible_net_spend,
            status="COMPLETED",
            accrual_status="ACCRUED" if points_to_accrue > 0 else "EXCLUDED",
            lines=order_lines,
        )
        db.add(order)
        await db.flush()

        tx_id = f"PTS-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        lot_id = f"LOT-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        if points_to_accrue > 0:
            # 7. Create PointsTransaction (Append-Only Journal)
            new_balance = account.current_balance + points_to_accrue
            accrual_tx = PointsTransaction(
                transaction_id=tx_id,
                account_id=account.account_id,
                order_id=order_id,
                related_transaction_id=None,
                rule_id=None,
                entry_type="ACCRUAL",
                points=points_to_accrue,
                running_balance=new_balance,
                idempotency_key=req.idempotency_key,
                notes=f"Points accrued for order {order_id} ({eligible_net_spend} qualifying spend @ {tier_multiplier}x)",
                created_at=now,
            )
            db.add(accrual_tx)
            await db.flush()

            # 8. Create FIFO PointsLot (365-day expiry)
            points_lot = PointsLot(
                lot_id=lot_id,
                transaction_id=tx_id,
                account_id=account.account_id,
                initial_points=points_to_accrue,
                remaining_points=points_to_accrue,
                status="ACTIVE",
                expires_at=lot_expires_at,
                created_at=now,
                updated_at=now,
            )
            db.add(points_lot)

            # 9. Update Account State atomically
            account.current_balance = new_balance
            account.lifetime_accrued += points_to_accrue
            account.qualifying_spend += eligible_net_spend
            account.updated_at = now
        else:
            new_balance = account.current_balance
            account.qualifying_spend += eligible_net_spend
            account.updated_at = now

        # 10. Audit Trail
        await AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="ORDER_ACCRUAL_COMPLETED",
            entity_type="orders",
            entity_id=order_id,
            metadata={
                "customer_id": customer.customer_id,
                "account_id": account.account_id,
                "points_accrued": points_to_accrue,
                "eligible_net_spend": str(eligible_net_spend),
                "tier_multiplier": str(tier_multiplier),
                "transaction_id": tx_id if points_to_accrue > 0 else None,
                "lot_id": lot_id if points_to_accrue > 0 else None,
            }
        )

        await db.commit()

        # Build response
        lines_response = [
            OrderLineResponse(
                order_line_id=l.order_line_id,
                order_id=l.order_id,
                line_number=l.line_number,
                sku=l.sku,
                product_name=l.product_name,
                category=l.category,
                quantity=l.quantity,
                unit_price=l.unit_price,
                item_discount=l.item_discount,
                net_amount=l.net_amount,
                is_eligible=l.is_eligible,
                created_at=l.created_at,
            )
            for l in order_lines
        ]

        return OrderAccrualResponse(
            order_id=order_id,
            customer_id=customer.customer_id,
            account_id=account.account_id,
            gross_amount=gross_order_amount,
            tax_amount=req.tax_amount,
            shipping_amount=req.shipping_amount,
            discount_amount=req.discount_amount,
            eligible_net_spend=eligible_net_spend,
            tier_id=account.tier_id,
            tier_multiplier=tier_multiplier,
            points_accrued=points_to_accrue,
            new_balance=new_balance,
            transaction_id=tx_id,
            lot_id=lot_id,
            lot_expires_at=lot_expires_at,
            lines=lines_response,
            created_at=now,
        )
