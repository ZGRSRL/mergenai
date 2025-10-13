from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Document
from ..schemas import ProposalDraft
from ..services.proposal.composer import generate_proposal_draft

router = APIRouter()


@router.post("/draft", response_model=ProposalDraft)
async def generate_draft_proposal(
    rfq_id: int,
    format: str = "json",  # json, docx, pdf
    db: Session = Depends(get_db)
):
    """Generate draft proposal for an RFQ"""
    
    # Check if RFQ exists
    rfq_doc = db.query(Document).filter(
        Document.id == rfq_id,
        Document.kind == "rfq"
    ).first()
    
    if not rfq_doc:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    # Generate proposal draft
    proposal = generate_proposal_draft(db, rfq_id)
    
    return proposal


@router.get("/draft/{rfq_id}/download")
async def download_proposal(
    rfq_id: int,
    format: str = "docx",
    db: Session = Depends(get_db)
):
    """Download proposal in specified format"""
    
    # Check if RFQ exists
    rfq_doc = db.query(Document).filter(
        Document.id == rfq_id,
        Document.kind == "rfq"
    ).first()
    
    if not rfq_doc:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    # Generate and return file
    if format == "docx":
        file_content = generate_proposal_draft(db, rfq_id, format="docx")
        return Response(
            content=file_content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=proposal_{rfq_id}.docx"}
        )
    elif format == "pdf":
        file_content = generate_proposal_draft(db, rfq_id, format="pdf")
        return Response(
            content=file_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=proposal_{rfq_id}.pdf"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")



