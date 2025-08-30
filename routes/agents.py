from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from dependencies import get_db, get_current_user
from models.agents import Agent
from models.state import State
from models.accounts import AccountsMaster
from schemas.agents import AgentCreate, AgentUpdate, AgentResponse, AgentWithStateResponse
from models.user import User
from decimal import Decimal
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def generate_agent_account_code(db: Session, agent_name: str) -> str:
    """Generate unique account code for agent automatically"""
    
    # Base code for agents (starting from 2105 series for Agent Commissions Payable)
    base_code = "2105"
    
    # Get the last agent account code to determine next sequence
    last_account = db.query(AccountsMaster).filter(
        AccountsMaster.account_code.like(f"{base_code}%")
    ).order_by(AccountsMaster.account_code.desc()).first()
    
    if last_account:
        # Extract number part and increment
        try:
            account_code = str(last_account.account_code)  # Convert to string first
            last_number = int(account_code[4:])  # Skip "2105" prefix
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
    
    # Generate new code with zero padding (3 digits for payable accounts)
    new_code = f"{base_code}{next_number:03d}"
    
    # Ensure uniqueness (in case of race conditions)
    while db.query(AccountsMaster).filter(AccountsMaster.account_code == new_code).first():
        next_number += 1
        new_code = f"{base_code}{next_number:03d}"
    
    return new_code


def create_agent_account(db: Session, agent_name: str, account_code: str):
    """Create associated payable account for the agent"""
    try:
        # Create account in chart of accounts - Agent is a payable account for commissions
        agent_account = AccountsMaster(
            account_code=account_code,
            account_name=f"Agent - {agent_name}",
            account_type="Liability",
            parent_account_code="2105",  # Parent: Agent Commissions Payable
            is_active=True,
            opening_balance=Decimal('0.00'),
            current_balance=Decimal('0.00'),
            description=f"Agent commission payable account for {agent_name}"
        )
        
        db.add(agent_account)
        db.commit()
        db.refresh(agent_account)
        
        logger.info(f"Created payable account {account_code} for agent {agent_name}")
        return agent_account
        
    except Exception as e:
        logger.error(f"Failed to create payable account for agent {agent_name}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create associated payable account: {str(e)}"
        )


@router.get("/", response_model=List[AgentWithStateResponse])
async def get_agents(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all agents with pagination and optional status filter"""
    query = db.query(Agent).options(joinedload(Agent.state))
    
    if status_filter:
        query = query.filter(Agent.status == status_filter)
    
    agents = query.offset(skip).limit(limit).all()
    
    # Format response with state information
    result = []
    for agent in agents:
        agent_data = AgentWithStateResponse.from_orm(agent)
        # Additional state fields from the relationship
        if agent.state:
            agent_data.state_name = agent.state.name
            agent_data.state_code = agent.state.code
            agent_data.gst_code = agent.state.gst_code
        result.append(agent_data)
    
    return result


@router.get("/{agent_id}", response_model=AgentWithStateResponse)
async def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific agent by ID"""
    agent = db.query(Agent).options(joinedload(Agent.state)).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent_data = AgentWithStateResponse.from_orm(agent)
    if agent.state:
        agent_data.state_name = agent.state.name
        agent_data.state_code = agent.state.code
        agent_data.gst_code = agent.state.gst_code
    
    return agent_data


@router.get("/code/{agent_acc_code}", response_model=AgentWithStateResponse)
async def get_agent_by_code(
    agent_acc_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific agent by account code"""
    agent = db.query(Agent).options(joinedload(Agent.state)).filter(Agent.agent_acc_code == agent_acc_code).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent_data = AgentWithStateResponse.from_orm(agent)
    if agent.state:
        agent_data.state_name = agent.state.name
        agent_data.state_code = agent.state.code
        agent_data.gst_code = agent.state.gst_code
    
    return agent_data


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new agent with automatic account creation"""
    
    # Validate state if provided
    if agent.state_id:
        state = db.query(State).filter(State.id == agent.state_id).first()
        if not state:
            raise HTTPException(status_code=400, detail="Invalid state ID")
    
    try:
        # Generate unique account code
        agent_acc_code = generate_agent_account_code(db, agent.agent_name)
        
        # Create the agent
        db_agent = Agent(
            **agent.dict(),
            agent_acc_code=agent_acc_code
        )
        
        db.add(db_agent)
        db.flush()  # Get the agent ID without committing
        
        # Create associated account
        create_agent_account(db, agent.agent_name, agent_acc_code)
        
        # Commit both agent and account
        db.commit()
        db.refresh(db_agent)
        
        logger.info(f"Successfully created agent {agent.agent_name} with account {agent_acc_code}")
        return db_agent
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create agent {agent.agent_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Validate state if provided
    if agent_update.state_id:
        state = db.query(State).filter(State.id == agent_update.state_id).first()
        if not state:
            raise HTTPException(status_code=400, detail="Invalid state ID")
    
    try:
        update_data = agent_update.dict(exclude_unset=True)
        
        # If agent name is being updated, update the associated account name too
        if 'agent_name' in update_data and update_data['agent_name'] != agent.agent_name:
            # Update associated account name
            associated_account = db.query(AccountsMaster).filter(
                AccountsMaster.account_code == agent.agent_acc_code
            ).first()
            
            if associated_account:
                setattr(associated_account, 'account_name', f"Agent - {update_data['agent_name']}")
                setattr(associated_account, 'description', f"Agent receivable account for {update_data['agent_name']}")
        
        # Update agent fields
        for field, value in update_data.items():
            setattr(agent, field, value)
        
        db.commit()
        db.refresh(agent)
        
        logger.info(f"Successfully updated agent {agent.agent_name}")
        return agent
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update agent {agent_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update agent: {str(e)}"
        )


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete an agent (set status to Inactive and deactivate associated account)"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        # Soft delete agent
        setattr(agent, 'status', 'Inactive')
        
        # Deactivate associated account
        associated_account = db.query(AccountsMaster).filter(
            AccountsMaster.account_code == agent.agent_acc_code
        ).first()
        
        if associated_account:
            setattr(associated_account, 'is_active', False)
        
        db.commit()
        
        logger.info(f"Successfully deactivated agent {agent.agent_name} and associated account")
        return {"message": f"Agent {agent.agent_name} deactivated successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete agent {agent_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deactivate agent: {str(e)}"
        )


@router.get("/status/{status}", response_model=List[AgentWithStateResponse])
async def get_agents_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all agents by status"""
    allowed_statuses = ['Active', 'Inactive', 'Suspended']
    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {', '.join(allowed_statuses)}"
        )
    
    agents = db.query(Agent).options(joinedload(Agent.state)).filter(Agent.status == status).all()
    
    result = []
    for agent in agents:
        agent_data = AgentWithStateResponse.from_orm(agent)
        if agent.state:
            agent_data.state_name = agent.state.name
            agent_data.state_code = agent.state.code
            agent_data.gst_code = agent.state.gst_code
        result.append(agent_data)
    
    return result


@router.get("/state/{state_id}", response_model=List[AgentWithStateResponse])
async def get_agents_by_state(
    state_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all agents by state"""
    # Validate state exists
    state = db.query(State).filter(State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    
    agents = db.query(Agent).options(joinedload(Agent.state)).filter(Agent.state_id == state_id).all()
    
    result = []
    for agent in agents:
        agent_data = AgentWithStateResponse.from_orm(agent)
        agent_data.state_name = agent.state.name
        agent_data.state_code = agent.state.code
        agent_data.gst_code = agent.state.gst_code
        result.append(agent_data)
    
    return result


@router.get("/public/count")
async def get_agents_count(db: Session = Depends(get_db)):
    """Public endpoint to get agents count (no auth required)"""
    total_agents = db.query(Agent).count()
    active_agents = db.query(Agent).filter(Agent.status == "Active").count()
    inactive_agents = db.query(Agent).filter(Agent.status == "Inactive").count()
    suspended_agents = db.query(Agent).filter(Agent.status == "Suspended").count()
    
    return {
        "total_agents": total_agents,
        "active_agents": active_agents,
        "inactive_agents": inactive_agents,
        "suspended_agents": suspended_agents
    }



