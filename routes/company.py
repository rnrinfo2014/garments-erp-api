from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from dependencies import get_db, get_current_active_user, require_admin
from models.company import CompanyDetails
from models.state import State
from models.user import User
from schemas.company import CompanyDetailsCreate, CompanyDetailsUpdate, CompanyDetailsResponse

router = APIRouter()

@router.get("/company-details", response_model=List[CompanyDetailsResponse])
async def get_company_details(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all company details."""
    companies = db.query(CompanyDetails).options(joinedload(CompanyDetails.state)).all()
    return companies

@router.get("/company-details/{company_id}", response_model=CompanyDetailsResponse)
async def get_company_detail(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get company details by ID."""
    company = db.query(CompanyDetails).options(joinedload(CompanyDetails.state)).filter(CompanyDetails.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company details not found")
    return company

@router.post("/company-details", response_model=CompanyDetailsResponse)
async def create_company_details(
    company: CompanyDetailsCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new company details (Admin/Superadmin only)."""
    # Validate state_id if provided
    if company.state_id:
        state = db.query(State).filter(State.id == company.state_id).first()
        if not state:
            raise HTTPException(status_code=400, detail="Invalid state ID")
    
    db_company = CompanyDetails(**company.dict())
    
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.put("/company-details/{company_id}", response_model=CompanyDetailsResponse)
async def update_company_details(
    company_id: int,
    company_update: CompanyDetailsUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update company details (Admin/Superadmin only)."""
    company = db.query(CompanyDetails).filter(CompanyDetails.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company details not found")
    
    # Create update dictionary with only non-None values
    update_data = {}
    if company_update.name is not None:
        update_data['name'] = company_update.name
    if company_update.address is not None:
        update_data['address'] = company_update.address
    if company_update.contact is not None:
        update_data['contact'] = company_update.contact
    if company_update.email is not None:
        update_data['email'] = company_update.email
    if company_update.gst is not None:
        update_data['gst'] = company_update.gst
    if company_update.website is not None:
        update_data['website'] = company_update.website
    if company_update.logo is not None:
        update_data['logo'] = company_update.logo
    if company_update.state_id is not None:
        # Validate state_id if provided
        if company_update.state_id:
            state = db.query(State).filter(State.id == company_update.state_id).first()
            if not state:
                raise HTTPException(status_code=400, detail="Invalid state ID")
        update_data['state_id'] = company_update.state_id
    
    # Perform the update if there's data to update
    if update_data:
        for key, value in update_data.items():
            setattr(company, key, value)
        db.commit()
        db.refresh(company)
    
    return company

@router.delete("/company-details/{company_id}")
async def delete_company_details(
    company_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete company details (Admin/Superadmin only)."""
    company = db.query(CompanyDetails).filter(CompanyDetails.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company details not found")
    
    db.delete(company)
    db.commit()
    return {"message": "Company details deleted successfully"}
