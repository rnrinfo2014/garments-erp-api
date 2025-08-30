from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from dependencies import get_db, get_current_active_user, require_admin
from models.state import State
from models.user import User
from schemas.state import StateCreate, StateUpdate, StateResponse

router = APIRouter()

@router.get("/states", response_model=List[StateResponse])
async def get_states(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all states."""
    states = db.query(State).order_by(State.name).all()
    return states

@router.get("/states/{state_id}", response_model=StateResponse)
async def get_state(
    state_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get state by ID."""
    state = db.query(State).filter(State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    return state

@router.post("/states", response_model=StateResponse)
async def create_state(
    state: StateCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new state (Admin/Superadmin only)."""
    # Check if state name already exists
    existing_state = db.query(State).filter(State.name == state.name).first()
    if existing_state:
        raise HTTPException(status_code=400, detail="State name already exists")
    
    # Check if state code already exists
    existing_code = db.query(State).filter(State.code == state.code).first()
    if existing_code:
        raise HTTPException(status_code=400, detail="State code already exists")
    
    # Check if GST code already exists
    existing_gst = db.query(State).filter(State.gst_code == state.gst_code).first()
    if existing_gst:
        raise HTTPException(status_code=400, detail="GST code already exists")
    
    db_state = State(**state.dict())
    
    db.add(db_state)
    db.commit()
    db.refresh(db_state)
    return db_state

@router.put("/states/{state_id}", response_model=StateResponse)
async def update_state(
    state_id: int,
    state_update: StateUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update state (Admin/Superadmin only)."""
    state = db.query(State).filter(State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    
    # Update fields using setattr to avoid SQLAlchemy column assignment issues
    if state_update.name is not None:
        # Check if new name is already taken by another state
        existing = db.query(State).filter(State.name == state_update.name, State.id != state_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="State name already taken")
        setattr(state, 'name', state_update.name)
    
    if state_update.code is not None:
        # Check if new code is already taken by another state
        existing = db.query(State).filter(State.code == state_update.code, State.id != state_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="State code already taken")
        setattr(state, 'code', state_update.code)
    
    if state_update.gst_code is not None:
        # Check if new GST code is already taken by another state
        existing = db.query(State).filter(State.gst_code == state_update.gst_code, State.id != state_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="GST code already taken")
        setattr(state, 'gst_code', state_update.gst_code)
    
    db.commit()
    db.refresh(state)
    return state

@router.delete("/states/{state_id}")
async def delete_state(
    state_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete state (Admin/Superadmin only)."""
    state = db.query(State).filter(State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    
    db.delete(state)
    db.commit()
    return {"message": "State deleted successfully"}
