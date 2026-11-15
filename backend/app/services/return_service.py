import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.app.models.loyalty import Order, OrderLine, OrderReturn, OrderReturnLine, Customer, LoyaltyAccount
from backend.app.models.ledger import PointsTransaction
from backend.app.schemas.loyalty import OrderReturnRequest, OrderReturnResponse
from backend.app.services.audit_service import AuditService
from backend.app.core.errors import NotFoundError, ConflictError, BadRequestError
from backend.app.core.logging import logger


class ReturnService:
    """
    Workflow E: Partial and Full Order Return Processing & Points Reversals.
    Enforces eligible refund spend reversal, cumulative reversal cap,
    and supports negative balances when returned items were previously redeemed (BR-10).
    """

    @classmethod
    async def process_return(
        cls,
        db: AsyncSession,
        req: OrderReturnRequest,
        actor_id: str,
    ) -> OrderReturnResponse:
        # 1. Idempotency check
        tx_chk = select(PointsTransaction).where(PointsTransaction.idempotency_key == req.idempotency_key)
        if (await db.execute(tx_chk)).scalar_one_or_none():
            raise ConflictError(detail=f"Return with idempotency key '{req.idempotency_key}' was already processed.")

        # 2. Retrieve Original Order with Lines and Customer/Account
        order_stmt = (
            select(Order)
            .options(
                selectinload(Order.lines),
                selectinload(Order.customer).selectinload(Customer.loyalty_account).selectinload(LoyaltyAccount.tier),
            )
            .where(Order.order_id == req.order_id)
        )
        order = (await db.execute(order_stmt)).scalar_one_or_none()
        if not order:
            await AuditService.log_rejection(
                db=db,
                actor_id=actor_id,
                operation_type="ORDER_RETURN",
                error_code="ORDER_NOT_FOUND",
                error_message=f"Order '{req.order_id}' does not exist.",
                payload={"order_id": req.order_id}
            )
            await db.commit()
            raise NotFoundError(detail=f"Order '{req.order_id}' not found.")

        customer = order.customer
        account = customer.loyalty_account
        tier_multiplier = account.tier.earning_multiplier if account.tier else Decimal("1.00")

        # 3. Locate Original Points Accrual Transaction for this Order
        orig_accrual_stmt = (
            select(PointsTransaction)
            .where(
                PointsTransaction.order_id == order.order_id,
                PointsTransaction.entry_type == "ACCRUAL",
            )
        )
        orig_accrual = (await db.execute(orig_accrual_stmt)).scalar_one_or_none()
        original_accrual_pts = orig_accrual.points if orig_accrual else 0

        # Calculate already reversed points on this order
        prev_rev_stmt = (
            select(func.coalesce(func.sum(PointsTransaction.points), 0))
            .where(
                PointsTransaction.order_id == order.order_id,
                PointsTransaction.entry_type == "REVERSAL",
            )
        )
        # Note: REVERSAL points are stored as negative numbers
        already_reversed_pts = abs((await db.execute(prev_rev_stmt)).scalar() or 0)
        remaining_reversible_pts = max(0, original_accrual_pts - already_reversed_pts)

        # 4. Validate Returned Lines
        order_lines_by_id = {line.order_line_id: line for line in order.lines}
        return_lines: List[OrderReturnLine] = []
        total_refund_amount = Decimal("0.00")
        total_eligible_refund = Decimal("0.00")

        return_id = req.return_id or f"RET-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Retrieve existing return lines for this order to verify quantity constraints
        existing_ret_stmt = (
            select(OrderReturnLine.order_line_id, func.sum(OrderReturnLine.quantity_returned))
            .join(OrderReturn, OrderReturn.return_id == OrderReturnLine.return_id)
            .where(OrderReturn.order_id == order.order_id)
            .group_by(OrderReturnLine.order_line_id)
        )
        existing_returns = dict((await db.execute(existing_ret_stmt)).all())

        for item in req.lines:
            orig_line = order_lines_by_id.get(item.order_line_id)
            if not orig_line:
                await AuditService.log_rejection(
                    db=db,
                    actor_id=actor_id,
                    operation_type="ORDER_RETURN",
                    error_code="INVALID_ORDER_LINE",
                    error_message=f"Order line '{item.order_line_id}' does not belong to order '{order.order_id}'.",
                    payload={"order_line_id": item.order_line_id}
                )
                await db.commit()
                raise BadRequestError(detail=f"Invalid order line '{item.order_line_id}'.")

            already_ret_qty = existing_returns.get(item.order_line_id, 0)
            available_qty = orig_line.quantity - already_ret_qty
            if item.quantity_returned > available_qty:
                await AuditService.log_rejection(
                    db=db,
                    actor_id=actor_id,
                    operation_type="ORDER_RETURN",
                    error_code="EXCESS_RETURN_QUANTITY",
                    error_message=f"Cannot return {item.quantity_returned} of {orig_line.sku}; only {available_qty} remaining.",
                    payload={"order_line_id": item.order_line_id, "requested": item.quantity_returned, "available": available_qty}
                )
                await db.commit()
                raise BadRequestError(
                    detail=f"Return quantity {item.quantity_returned} exceeds available quantity {available_qty} for {orig_line.sku}."
                )

            # Calculate proportional refund for this line
            unit_net = orig_line.net_amount / orig_line.quantity if orig_line.quantity > 0 else Decimal("0.00")
            line_refund = round(unit_net * item.quantity_returned, 2)
            total_refund_amount += line_refund

            if orig_line.is_eligible:
                total_eligible_refund += line_refund

            ret_line = OrderReturnLine(
                return_line_id=f"RLINE-{return_id}-{len(return_lines) + 1:02d}",
                return_id=return_id,
                order_line_id=item.order_line_id,
                quantity_returned=item.quantity_returned,
                refund_amount=line_refund,
            )
            return_lines.append(ret_line)

        # 5. Compute Points to Reverse with Floor Rounding (BR-02 & BR-10)
        # points = min(floor(eligible_refund * tier_multiplier), remaining_reversible_pts)
        pts_calculated = math.floor(float(total_eligible_refund * tier_multiplier))
        points_to_reverse = min(pts_calculated, remaining_reversible_pts)

        # 6. Determine Return Type
        total_order_qty = sum(l.quantity for l in order.lines)
        total_returned_qty = sum(r.quantity_returned for r in return_lines) + sum(existing_returns.values())
        return_type = "FULL" if total_returned_qty >= total_order_qty else "PARTIAL"

        now = datetime.now(timezone.utc)
        order_return = OrderReturn(
            return_id=return_id,
            order_id=order.order_id,
            return_type=return_type,
            total_refund_amount=total_refund_amount,
            points_reversed=points_to_reverse,
            status="PROCESSED",
            created_at=now,
            lines=return_lines,
        )
        db.add(order_return)
        await db.flush()

        tx_id = f"PTS-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        # 7. Append Compensating Reversal Transaction
        new_balance = account.current_balance - points_to_reverse
        reversal_tx = PointsTransaction(
            transaction_id=tx_id,
            account_id=account.account_id,
            order_id=order.order_id,
            related_transaction_id=orig_accrual.transaction_id if orig_accrual else None,
            rule_id=None,
            entry_type="REVERSAL",
            points=-points_to_reverse,
            running_balance=new_balance,
            idempotency_key=req.idempotency_key,
            notes=f"Reversal of {points_to_reverse} points for return {return_id} (order {order.order_id})",
            created_at=now,
        )
        db.add(reversal_tx)

        # 8. Update Account Balance & Qualifying Spend (Negative Balance Allowed per BR-10)
        account.current_balance = new_balance
        account.qualifying_spend = max(Decimal("0.00"), account.qualifying_spend - total_eligible_refund)
        account.updated_at = now

        # Update order status if full return
        if return_type == "FULL":
            order.status = "RETURNED"

        # 9. Audit Trail
        await AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="ORDER_RETURN_PROCESSED",
            entity_type="order_returns",
            entity_id=return_id,
            metadata={
                "order_id": order.order_id,
                "account_id": account.account_id,
                "return_type": return_type,
                "refund_amount": str(total_refund_amount),
                "points_reversed": points_to_reverse,
                "new_balance": new_balance,
                "is_balance_negative": new_balance < 0,
                "transaction_id": tx_id,
            }
        )

        await db.commit()

        return OrderReturnResponse(
            return_id=return_id,
            order_id=order.order_id,
            return_type=return_type,
            total_refund_amount=total_refund_amount,
            points_reversed=points_to_reverse,
            new_balance=new_balance,
            status="PROCESSED",
            reversal_transaction_id=tx_id,
            is_balance_negative=(new_balance < 0),
            redemptions_frozen=(new_balance < 0),
            created_at=now,
        )
