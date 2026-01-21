"""WebSocket endpoint for real-time progress updates during file organization."""

from typing import Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models import Operation
from src.backend.middleware.auth import get_current_user

router = APIRouter(prefix="/ws", tags=["websocket"])

# Keep track of active WebSocket connections
active_connections: Set[WebSocket] = set()


@router.websocket("/operations/{operation_id}")
async def websocket_operation_progress(
    websocket: WebSocket,
    operation_id: str,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for real-time operation progress.
    
    Client connects and receives progress updates as background job processes files.
    
    Sends JSON messages:
        {
            "type": "progress",
            "files_scanned": 1000,
            "files_processed": 500,
            "duplicates_found": 23,
            "space_saved_bytes": 1073741824
        }
        
        {
            "type": "completed",
            "status": "completed",
            "files_scanned": 1000,
            "files_processed": 500,
            "duplicates_found": 23,
            "space_saved_bytes": 1073741824
        }
        
        {
            "type": "error",
            "error": "Permission denied on file xyz"
        }
    """
    await websocket.accept()
    
    try:
        operation_uuid = UUID(operation_id)
    except ValueError:
        await websocket.send_json({"type": "error", "error": "Invalid operation ID"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    active_connections.add(websocket)
    
    try:
        # Verify operation exists
        operation = db.query(Operation).filter(Operation.id == operation_uuid).first()
        if not operation:
            await websocket.send_json({"type": "error", "error": "Operation not found"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "status": operation.status.value,
            "files_scanned": operation.files_scanned,
            "files_processed": operation.files_processed,
            "duplicates_found": operation.duplicates_found,
            "space_saved_bytes": operation.space_saved_bytes,
        })
        
        # Keep connection open and poll for updates
        import asyncio
        
        while True:
            # Check operation status every 500ms
            await asyncio.sleep(0.5)
            
            # Refresh operation from database
            db.refresh(operation)
            
            # Send progress update
            await websocket.send_json({
                "type": "progress",
                "status": operation.status.value,
                "files_scanned": operation.files_scanned,
                "files_processed": operation.files_processed,
                "duplicates_found": operation.duplicates_found,
                "space_saved_bytes": operation.space_saved_bytes,
            })
            
            # If operation is complete, send completion and close
            if operation.is_complete:
                await websocket.send_json({
                    "type": "completed",
                    "status": operation.status.value,
                    "files_scanned": operation.files_scanned,
                    "files_processed": operation.files_processed,
                    "duplicates_found": operation.duplicates_found,
                    "space_saved_bytes": operation.space_saved_bytes,
                    "error": operation.error_message,
                })
                break
    
    except WebSocketDisconnect:
        # Client disconnected
        pass
    
    except Exception as e:
        await websocket.send_json({"type": "error", "error": str(e)})
    
    finally:
        active_connections.discard(websocket)
        await websocket.close()


async def broadcast_progress(operation_id: UUID, progress_data: dict):
    """Broadcast progress update to all connected WebSocket clients.
    
    This could be called from background jobs to push updates.
    
    Args:
        operation_id: Operation UUID
        progress_data: Progress data to broadcast
    """
    for connection in active_connections:
        try:
            await connection.send_json({
                "type": "progress",
                "operation_id": str(operation_id),
                **progress_data,
            })
        except Exception:
            # Connection closed or other error, will be cleaned up
            pass
