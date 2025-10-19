from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# Базовые схемы
class ElectionBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    is_active: bool = True

class PollBase(BaseModel):
    election_id: int
    title: str
    description: Optional[str] = None
    max_votes_per_voter: int = 1
    is_active: bool = True

class CandidateBase(BaseModel):
    poll_id: int
    name: str
    description: Optional[str] = None

class VoterBase(BaseModel):
    email: str
    name: str
    is_verified: bool = False

class VoteBase(BaseModel):
    poll_id: int
    candidate_id: int
    voter_id: int

# Схемы для создания
class ElectionCreate(ElectionBase):
    pass

class PollCreate(PollBase):
    pass

class CandidateCreate(CandidateBase):
    pass

class VoterCreate(VoterBase):
    pass

class VoteCreate(VoteBase):
    pass

# Схемы для ответов
class ElectionResponse(ElectionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PollResponse(PollBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class VoterResponse(VoterBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class VoteResponse(VoteBase):
    id: int
    voted_at: datetime
    
    class Config:
        from_attributes = True

# Схемы с отношениями
class CandidateWithVotes(CandidateResponse):
    votes_count: int = 0

class PollWithCandidates(PollResponse):
    candidates: List[CandidateWithVotes] = []
    total_votes: int = 0

class ElectionWithPolls(ElectionResponse):
    polls: List[PollWithCandidates] = []