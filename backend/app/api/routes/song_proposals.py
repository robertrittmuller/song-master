from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.db.deps import get_db
from backend.app.models import SongProposal
from backend.app.schemas import (
    SongProposalGenerate,
    SongProposalGenerateResponse,
    SongProposalRead,
)
from backend.app.services.song_proposal_service import generate_song_proposal_ideas

router = APIRouter(prefix="/api/song-proposals", tags=["song-proposals"])


@router.get("", response_model=List[SongProposalRead])
def list_song_proposals(db: Session = Depends(get_db)) -> List[SongProposalRead]:
    return db.query(SongProposal).order_by(SongProposal.created_at.desc()).all()


@router.post("/generate", response_model=SongProposalGenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_song_proposals(
    payload: SongProposalGenerate,
    db: Session = Depends(get_db),
) -> SongProposalGenerateResponse:
    try:
        generated_proposals = generate_song_proposal_ideas(
            payload.source_prompt.strip(),
            payload.count,
            payload.use_local,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    proposals = [
        SongProposal(
            title=proposal["title"],
            prompt=proposal["prompt"],
            source_prompt=payload.source_prompt.strip(),
            use_local=payload.use_local,
            status="open",
        )
        for proposal in generated_proposals
    ]

    db.add_all(proposals)
    db.commit()
    for proposal in proposals:
        db.refresh(proposal)

    return SongProposalGenerateResponse(proposals=proposals)


@router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song_proposal(proposal_id: int, db: Session = Depends(get_db)) -> Response:
    proposal = db.get(SongProposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song proposal not found")

    db.delete(proposal)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
