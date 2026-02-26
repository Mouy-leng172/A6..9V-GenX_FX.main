"""
HTTP REST API endpoints for MetaTrader Expert Advisor (EA) communication.
Provides endpoints for EA registration, signal retrieval, heartbeat, and trade reporting.
"""

import hashlib
import logging
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..utils.ea_auth import validate_ea_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["ea_http"])

# In-memory storage for EA connections and signals
# In production, this should use Redis or a database
ea_connections: Dict[str, Dict[str, Any]] = {}
pending_signals: Deque[Dict[str, Any]] = deque()
trade_results: Deque[Dict[str, Any]] = deque(maxlen=10000)


def get_or_create_ea_id(data: Dict[str, Any]) -> str:
    """
    Extract or create EA identifier from message data.
    Uses account number and magic number if available, otherwise creates a temporary ID.
    """
    # Try to extract from various possible data structures
    account = data.get("account") or data.get("account_number")
    magic = data.get("magic_number") or data.get("magic")

    if account and magic:
        return f"{account}_{magic}"

    # Fallback to a default ID if we can't identify the EA
    # In production, this should be handled by requiring proper authentication
    return "default_ea"


# Pydantic models for request/response validation
class EAInfo(BaseModel):
    """Expert Advisor information"""

    name: str
    version: str
    account: int
    broker: str
    symbol: str
    timeframe: str
    magic_number: int


class HeartbeatData(BaseModel):
    """EA heartbeat data"""

    status: str
    positions: int
    pending_orders: int
    last_signal: str


class AccountStatusData(BaseModel):
    """Account status information"""

    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    profit: float
    open_positions: int


class TradeResultData(BaseModel):
    """Trade execution result"""

    signal_id: str
    ticket: int
    success: bool
    error_code: int
    error_message: str
    execution_price: float
    slippage: float


class MessageRequest(BaseModel):
    """Generic message wrapper"""

    type: str
    data: Dict[str, Any]
    timestamp: str


@router.get("/ping")
async def ping():
    """
    Health check endpoint for EA connectivity testing.

    Returns:
        dict: Status message indicating server is alive
    """
    return {
        "status": "ok",
        "message": "GenX AI Server is running",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/get_signal")
async def get_signal(api_key: str = Depends(validate_ea_api_key)):
    """
    Retrieve the next pending trading signal for the EA.

    Security:
        Requires valid API key in X-API-Key header

    Returns:
        dict: Trading signal if available, or 204 No Content status
    """
    if not pending_signals:
        # Return 204 No Content when no signals are available
        return {"type": "NO_SIGNAL", "message": "No pending signals"}

    # Get the oldest signal (FIFO)
    signal = pending_signals.popleft()
    logger.info(f"Signal retrieved by authenticated EA: {signal}")

    return {
        "type": "SIGNAL",
        "data": signal,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/ea_info")
async def ea_info(request: MessageRequest, api_key: str = Depends(validate_ea_api_key)):
    """
    Register or update EA information with the server.

    Security:
        Requires valid API key in X-API-Key header

    Args:
        request: Message containing EA information
        api_key: Validated API key from header

    Returns:
        dict: Confirmation message
    """
    try:
        ea_data = request.data
        ea_id = f"{ea_data.get('account')}_{ea_data.get('magic_number')}"

        # Create API key hash for audit purposes (SHA-256, full hash for security)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Store EA connection info
        ea_connections[ea_id] = {
            "info": ea_data,
            "last_seen": datetime.utcnow(),
            "status": "connected",
            "api_key_hash": api_key_hash,  # Store full hash for secure audit trail
        }

        logger.info(
            f"EA registered: {ea_data.get('name')} v{ea_data.get('version')} "
            f"(Account: {ea_data.get('account')}, Magic: {ea_data.get('magic_number')})"
        )

        return {
            "status": "success",
            "message": "EA information received",
            "ea_id": ea_id,
        }
    except Exception as e:
        logger.error(f"Error processing EA info: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/heartbeat")
async def heartbeat(
    request: MessageRequest, api_key: str = Depends(validate_ea_api_key)
):
    """
    Receive heartbeat from EA to maintain connection status.

    Security:
        Requires valid API key in X-API-Key header

    Args:
        request: Message containing heartbeat data
        api_key: Validated API key from header

    Returns:
        dict: Acknowledgment message
    """
    try:
        heartbeat_data = request.data

        # Identify the specific EA sending the heartbeat
        ea_id = get_or_create_ea_id(heartbeat_data)

        # Update or create EA connection record
        if ea_id not in ea_connections:
            ea_connections[ea_id] = {"status": "connected"}

        ea_connections[ea_id]["last_seen"] = datetime.utcnow()
        ea_connections[ea_id]["heartbeat"] = heartbeat_data

        logger.debug(
            f"Heartbeat received from authenticated EA {ea_id}: {heartbeat_data}"
        )

        return {
            "status": "success",
            "message": "Heartbeat acknowledged",
            "ea_id": ea_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/account_status")
async def account_status(
    request: MessageRequest, api_key: str = Depends(validate_ea_api_key)
):
    """
    Receive and store account status information from EA.

    Security:
        Requires valid API key in X-API-Key header

    Args:
        request: Message containing account status data
        api_key: Validated API key from header

    Returns:
        dict: Acknowledgment message
    """
    try:
        status_data = request.data

        # Identify the specific EA sending the status
        ea_id = get_or_create_ea_id(status_data)

        # Update or create EA connection record
        if ea_id not in ea_connections:
            ea_connections[ea_id] = {"status": "connected"}

        ea_connections[ea_id]["account_status"] = status_data
        ea_connections[ea_id]["last_status_update"] = datetime.utcnow()

        logger.info(
            f"Account status received from authenticated EA {ea_id} - Balance: {status_data.get('balance')}, "
            f"Equity: {status_data.get('equity')}, "
            f"Positions: {status_data.get('open_positions')}"
        )

        return {
            "status": "success",
            "message": "Account status received",
            "ea_id": ea_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error processing account status: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trade_result")
async def trade_result(
    request: MessageRequest, api_key: str = Depends(validate_ea_api_key)
):
    """
    Receive trade execution results from EA.

    Security:
        Requires valid API key in X-API-Key header

    Args:
        request: Message containing trade execution result
        api_key: Validated API key from header

    Returns:
        dict: Acknowledgment message
    """
    try:
        result_data = request.data

        # Store trade result
        trade_results.append(
            {**result_data, "received_at": datetime.utcnow().isoformat()}
        )

        if result_data.get("success"):
            logger.info(
                f"Trade executed successfully - Signal: {result_data.get('signal_id')}, "
                f"Ticket: {result_data.get('ticket')}, "
                f"Price: {result_data.get('execution_price')}"
            )
        else:
            logger.warning(
                f"Trade execution failed - Signal: {result_data.get('signal_id')}, "
                f"Error: {result_data.get('error_message')} "
                f"(Code: {result_data.get('error_code')})"
            )

        return {
            "status": "success",
            "message": "Trade result received",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error processing trade result: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Admin/monitoring endpoints
@router.get("/ea_status")
async def get_ea_status(api_key: str = Depends(validate_ea_api_key)):
    """
    Get status of all connected EAs (admin endpoint).

    Security:
        Requires valid API key in X-API-Key header

    Returns:
        dict: Status information for all connected EAs
    """
    return {
        "connected_eas": len(ea_connections),
        "eas": ea_connections,
        "pending_signals": len(pending_signals),
        "trade_results_count": len(trade_results),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/send_signal")
async def send_signal(
    signal: Dict[str, Any], api_key: str = Depends(validate_ea_api_key)
):
    """
    Add a new trading signal to the queue (admin/internal endpoint).

    Security:
        Requires valid API key in X-API-Key header

    Args:
        signal: Trading signal data
        api_key: Validated API key from header

    Returns:
        dict: Confirmation message
    """
    try:
        # Add signal to pending queue
        pending_signals.append(signal)

        logger.info(
            f"Signal added to queue by authenticated client: {signal.get('action')} "
            f"{signal.get('instrument')} {signal.get('volume')}"
        )

        return {
            "status": "success",
            "message": "Signal added to queue",
            "signal_id": signal.get("signal_id"),
            "queue_position": len(pending_signals),
        }
    except Exception as e:
        logger.error(f"Error adding signal: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/trade_results")
async def get_trade_results(
    limit: int = 100, api_key: str = Depends(validate_ea_api_key)
):
    """
    Get recent trade execution results (admin endpoint).

    Security:
        Requires valid API key in X-API-Key header

    Args:
        limit: Maximum number of results to return
        api_key: Validated API key from header

    Returns:
        dict: Recent trade results
    """
    return {
        # Convert deque to list for slicing
        "results": list(trade_results)[-limit:],
        "total_count": len(trade_results),
        "timestamp": datetime.utcnow().isoformat(),
    }
