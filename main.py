from fastapi import FastAPI, HTTPException, Depends
from peewee import fn
from models import (
    Election, Poll, Candidate, Voter, Vote, 
    create_tables, DBContext
)
from schemas import (
    ElectionCreate, ElectionResponse, ElectionWithPolls,
    PollCreate, PollResponse, PollWithCandidates,
    CandidateCreate, CandidateResponse, CandidateWithVotes,
    VoterCreate, VoterResponse,
    VoteCreate, VoteResponse
)
from datetime import datetime

app = FastAPI(
    title="Voting System API", 
    version="1.0.0",
    description="Система проведения онлайн-голосований с использованием FastAPI и SQLite"
)

# Создаем таблицы при запуске
@app.on_event("startup")
def startup():
    create_tables()
    print("🚀 Voting System API запущен")

# Health check endpoint
@app.get("/")
def read_root():
    """Проверка работоспособности API"""
    return {
        "message": "Voting System API", 
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
def health_check():
    """Проверка здоровья системы"""
    with DBContext():
        try:
            # Проверяем подключение к БД
            Election.select().limit(1).count()
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# CRUD для Election (Избирательные кампании)
@app.post("/elections/", response_model=ElectionResponse, status_code=201)
def create_election(election: ElectionCreate):
    """Создать новую избирательную кампанию"""
    with DBContext():
        # Проверяем даты
        if election.start_date >= election.end_date:
            raise HTTPException(
                status_code=400, 
                detail="Дата начала должна быть раньше даты окончания"
            )
        
        election_db = Election.create(**election.dict())
        return ElectionResponse.from_orm(election_db)

@app.get("/elections/", response_model=list[ElectionResponse])
def read_elections(skip: int = 0, limit: int = 100, active_only: bool = False):
    """Получить список избирательных кампаний"""
    with DBContext():
        query = Election.select()
        if active_only:
            query = query.where(Election.is_active == True)
        
        elections = query.offset(skip).limit(limit)
        return [ElectionResponse.from_orm(election) for election in elections]

@app.get("/elections/{election_id}", response_model=ElectionWithPolls)
def read_election(election_id: int):
    """Получить избирательную кампанию по ID с голосованиями и статистикой"""
    with DBContext():
        try:
            election = Election.get(Election.id == election_id)
            
            # Получаем голосования с кандидатами и количеством голосов
            polls_data = []
            for poll in election.polls:
                candidates_with_votes = []
                total_votes = 0
                
                for candidate in poll.candidates:
                    votes_count = Vote.select().where(Vote.candidate == candidate).count()
                    candidate_data = CandidateWithVotes.from_orm(candidate)
                    candidate_data.votes_count = votes_count
                    candidates_with_votes.append(candidate_data)
                    total_votes += votes_count
                
                poll_data = PollWithCandidates.from_orm(poll)
                poll_data.candidates = candidates_with_votes
                poll_data.total_votes = total_votes
                polls_data.append(poll_data)
            
            election_data = ElectionWithPolls.from_orm(election)
            election_data.polls = polls_data
            return election_data
            
        except Election.DoesNotExist:
            raise HTTPException(status_code=404, detail="Избирательная кампания не найдена")

@app.put("/elections/{election_id}", response_model=ElectionResponse)
def update_election(election_id: int, election: ElectionCreate):
    """Обновить избирательную кампанию"""
    with DBContext():
        try:
            election_db = Election.get(Election.id == election_id)
            
            # Проверяем даты
            if election.start_date >= election.end_date:
                raise HTTPException(
                    status_code=400, 
                    detail="Дата начала должна быть раньше даты окончания"
                )
            
            for key, value in election.dict().items():
                setattr(election_db, key, value)
            election_db.save()
            return ElectionResponse.from_orm(election_db)
            
        except Election.DoesNotExist:
            raise HTTPException(status_code=404, detail="Избирательная кампания не найдена")

@app.delete("/elections/{election_id}")
def delete_election(election_id: int):
    """Удалить избирательную кампанию"""
    with DBContext():
        try:
            election = Election.get(Election.id == election_id)
            election.delete_instance()
            return {"message": "Избирательная кампания успешно удалена"}
        except Election.DoesNotExist:
            raise HTTPException(status_code=404, detail="Избирательная кампания не найдена")

# CRUD для Poll (Голосования)
@app.post("/polls/", response_model=PollResponse, status_code=201)
def create_poll(poll: PollCreate):
    """Создать новое голосование"""
    with DBContext():
        try:
            # Проверяем существование избирательной кампании
            Election.get(Election.id == poll.election_id)
            
            poll_db = Poll.create(**poll.dict())
            return PollResponse.from_orm(poll_db)
            
        except Election.DoesNotExist:
            raise HTTPException(status_code=404, detail="Избирательная кампания не найдена")

@app.get("/polls/", response_model=list[PollResponse])
def read_polls(skip: int = 0, limit: int = 100, active_only: bool = False):
    """Получить список голосований"""
    with DBContext():
        query = Poll.select()
        if active_only:
            query = query.where(Poll.is_active == True)
        
        polls = query.offset(skip).limit(limit)
        return [PollResponse.from_orm(poll) for poll in polls]

@app.get("/polls/{poll_id}", response_model=PollWithCandidates)
def read_poll(poll_id: int):
    """Получить голосование по ID с кандидатами и статистикой"""
    with DBContext():
        try:
            poll = Poll.get(Poll.id == poll_id)
            
            candidates_with_votes = []
            total_votes = 0
            
            for candidate in poll.candidates:
                votes_count = Vote.select().where(Vote.candidate == candidate).count()
                candidate_data = CandidateWithVotes.from_orm(candidate)
                candidate_data.votes_count = votes_count
                candidates_with_votes.append(candidate_data)
                total_votes += votes_count
            
            poll_data = PollWithCandidates.from_orm(poll)
            poll_data.candidates = candidates_with_votes
            poll_data.total_votes = total_votes
            
            return poll_data
            
        except Poll.DoesNotExist:
            raise HTTPException(status_code=404, detail="Голосование не найдено")

@app.put("/polls/{poll_id}", response_model=PollResponse)
def update_poll(poll_id: int, poll: PollCreate):
    """Обновить голосование"""
    with DBContext():
        try:
            poll_db = Poll.get(Poll.id == poll_id)
            
            # Проверяем существование избирательной кампании
            Election.get(Election.id == poll.election_id)
            
            for key, value in poll.dict().items():
                setattr(poll_db, key, value)
            poll_db.save()
            return PollResponse.from_orm(poll_db)
            
        except Poll.DoesNotExist:
            raise HTTPException(status_code=404, detail="Голосование не найдено")
        except Election.DoesNotExist:
            raise HTTPException(status_code=404, detail="Избирательная кампания не найдена")

@app.delete("/polls/{poll_id}")
def delete_poll(poll_id: int):
    """Удалить голосование"""
    with DBContext():
        try:
            poll = Poll.get(Poll.id == poll_id)
            poll.delete_instance()
            return {"message": "Голосование успешно удалено"}
        except Poll.DoesNotExist:
            raise HTTPException(status_code=404, detail="Голосование не найдено")

# CRUD для Candidate (Кандидаты)
@app.post("/candidates/", response_model=CandidateResponse, status_code=201)
def create_candidate(candidate: CandidateCreate):
    """Создать нового кандидата"""
    with DBContext():
        try:
            # Проверяем существование голосования
            Poll.get(Poll.id == candidate.poll_id)
            
            candidate_db = Candidate.create(**candidate.dict())
            return CandidateResponse.from_orm(candidate_db)
            
        except Poll.DoesNotExist:
            raise HTTPException(status_code=404, detail="Голосование не найдено")

@app.get("/candidates/", response_model=list[CandidateResponse])
def read_candidates(skip: int = 0, limit: int = 100, poll_id: int = None):
    """Получить список кандидатов"""
    with DBContext():
        query = Candidate.select()
        if poll_id:
            query = query.where(Candidate.poll == poll_id)
        
        candidates = query.offset(skip).limit(limit)
        return [CandidateResponse.from_orm(candidate) for candidate in candidates]

@app.get("/candidates/{candidate_id}", response_model=CandidateResponse)
def read_candidate(candidate_id: int):
    """Получить кандидата по ID"""
    with DBContext():
        try:
            candidate = Candidate.get(Candidate.id == candidate_id)
            return CandidateResponse.from_orm(candidate)
        except Candidate.DoesNotExist:
            raise HTTPException(status_code=404, detail="Кандидат не найден")

@app.put("/candidates/{candidate_id}", response_model=CandidateResponse)
def update_candidate(candidate_id: int, candidate: CandidateCreate):
    """Обновить кандидата"""
    with DBContext():
        try:
            candidate_db = Candidate.get(Candidate.id == candidate_id)
            
            # Проверяем существование голосования
            Poll.get(Poll.id == candidate.poll_id)
            
            for key, value in candidate.dict().items():
                setattr(candidate_db, key, value)
            candidate_db.save()
            return CandidateResponse.from_orm(candidate_db)
            
        except Candidate.DoesNotExist:
            raise HTTPException(status_code=404, detail="Кандидат не найден")
        except Poll.DoesNotExist:
            raise HTTPException(status_code=404, detail="Голосование не найдено")

@app.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: int):
    """Удалить кандидата"""
    with DBContext():
        try:
            candidate = Candidate.get(Candidate.id == candidate_id)
            candidate.delete_instance()
            return {"message": "Кандидат успешно удален"}
        except Candidate.DoesNotExist:
            raise HTTPException(status_code=404, detail="Кандидат не найден")

# CRUD для Voter (Избиратели)
@app.post("/voters/", response_model=VoterResponse, status_code=201)
def create_voter(voter: VoterCreate):
    """Создать нового избирателя"""
    with DBContext():
        try:
            voter_db = Voter.create(**voter.dict())
            return VoterResponse.from_orm(voter_db)
        except Exception as e:
            if "unique" in str(e).lower():
                raise HTTPException(status_code=400, detail="Избиратель с таким email уже существует")
            raise HTTPException(status_code=400, detail="Ошибка при создании избирателя")

@app.get("/voters/", response_model=list[VoterResponse])
def read_voters(skip: int = 0, limit: int = 100, verified_only: bool = False):
    """Получить список избирателей"""
    with DBContext():
        query = Voter.select()
        if verified_only:
            query = query.where(Voter.is_verified == True)
        
        voters = query.offset(skip).limit(limit)
        return [VoterResponse.from_orm(voter) for voter in voters]

@app.get("/voters/{voter_id}", response_model=VoterResponse)
def read_voter(voter_id: int):
    """Получить избирателя по ID"""
    with DBContext():
        try:
            voter = Voter.get(Voter.id == voter_id)
            return VoterResponse.from_orm(voter)
        except Voter.DoesNotExist:
            raise HTTPException(status_code=404, detail="Избиратель не найден")

@app.put("/voters/{voter_id}", response_model=VoterResponse)
def update_voter(voter_id: int, voter: VoterCreate):
    """Обновить избирателя"""
    with DBContext():
        try:
            voter_db = Voter.get(Voter.id == voter_id)
            
            for key, value in voter.dict().items():
                setattr(voter_db, key, value)
            voter_db.save()
            return VoterResponse.from_orm(voter_db)
            
        except Voter.DoesNotExist:
            raise HTTPException(status_code=404, detail="Избиратель не найден")
        except Exception as e:
            if "unique" in str(e).lower():
                raise HTTPException(status_code=400, detail="Избиратель с таким email уже существует")
            raise HTTPException(status_code=400, detail="Ошибка при обновлении избирателя")

@app.delete("/voters/{voter_id}")
def delete_voter(voter_id: int):
    """Удалить избирателя"""
    with DBContext():
        try:
            voter = Voter.get(Voter.id == voter_id)
            voter.delete_instance()
            return {"message": "Избиратель успешно удален"}
        except Voter.DoesNotExist:
            raise HTTPException(status_code=404, detail="Избиратель не найден")

# Голосование
@app.post("/votes/", response_model=VoteResponse, status_code=201)
def create_vote(vote: VoteCreate):
    """Проголосовать"""
    with DBContext():
        try:
            # Проверяем существование сущностей
            poll = Poll.get(Poll.id == vote.poll_id)
            candidate = Candidate.get(Candidate.id == vote.candidate_id)
            voter = Voter.get(Voter.id == vote.voter_id)
            
            # Проверяем, что кандидат принадлежит голосованию
            if candidate.poll.id != poll.id:
                raise HTTPException(
                    status_code=400, 
                    detail="Кандидат не принадлежит указанному голосованию"
                )
            
            # Проверяем, не голосовал ли уже этот избиратель в этом голосовании
            existing_vote = Vote.select().where(
                (Vote.poll == poll) & (Vote.voter == voter)
            ).first()
            
            if existing_vote:
                raise HTTPException(
                    status_code=400, 
                    detail="Избиратель уже голосовал в этом голосовании"
                )
            
            # Проверяем активность голосования
            if not poll.is_active:
                raise HTTPException(status_code=400, detail="Голосование не активно")
            
            # Проверяем верификацию избирателя
            if not voter.is_verified:
                raise HTTPException(
                    status_code=400, 
                    detail="Избиратель не верифицирован"
                )
            
            # Проверяем даты избирательной кампании
            election = poll.election
            now = datetime.now()
            if now < election.start_date or now > election.end_date:
                raise HTTPException(
                    status_code=400, 
                    detail="Голосование в данной кампании сейчас недоступно"
                )
            
            # Создаем голос
            vote_db = Vote.create(**vote.dict())
            return VoteResponse.from_orm(vote_db)
            
        except Poll.DoesNotExist:
            raise HTTPException(status_code=404, detail="Голосование не найдено")
        except Candidate.DoesNotExist:
            raise HTTPException(status_code=404, detail="Кандидат не найден")
        except Voter.DoesNotExist:
            raise HTTPException(status_code=404, detail="Избиратель не найден")

@app.get("/votes/", response_model=list[VoteResponse])
def read_votes(skip: int = 0, limit: int = 100, poll_id: int = None):
    """Получить список голосов"""
    with DBContext():
        query = Vote.select()
        if poll_id:
            query = query.where(Vote.poll == poll_id)
        
        votes = query.offset(skip).limit(limit)
        return [VoteResponse.from_orm(vote) for vote in votes]

# Статистика и результаты
@app.get("/polls/{poll_id}/results")
def get_poll_results(poll_id: int):
    """Получить результаты голосования"""
    with DBContext():
        try:
            poll = Poll.get(Poll.id == poll_id)
            
            results = []
            total_votes = 0
            
            for candidate in poll.candidates:
                votes_count = Vote.select().where(Vote.candidate == candidate).count()
                percentage = (votes_count / Vote.select().where(Vote.poll == poll).count() * 100) if Vote.select().where(Vote.poll == poll).count() > 0 else 0
                
                results.append({
                    "candidate_id": candidate.id,
                    "candidate_name": candidate.name,
                    "candidate_description": candidate.description,
                    "votes": votes_count,
                    "percentage": round(percentage, 2)
                })
                total_votes += votes_count
            
            # Сортируем по количеству голосов (по убыванию)
            results.sort(key=lambda x: x["votes"], reverse=True)
            
            return {
                "poll_id": poll.id,
                "poll_title": poll.title,
                "total_votes": total_votes,
                "unique_voters": Vote.select().where(Vote.poll == poll).count(),
                "results": results
            }
            
        except Poll.DoesNotExist:
            raise HTTPException(status_code=404, detail="Голосование не найдено")

@app.get("/elections/{election_id}/stats")
def get_election_stats(election_id: int):
    """Получить статистику по избирательной кампании"""
    with DBContext():
        try:
            election = Election.get(Election.id == election_id)
            
            total_polls = election.polls.count()
            total_votes = 0
            total_voters = Vote.select().where(Vote.poll.in_(election.polls)).count()
            
            polls_stats = []
            for poll in election.polls:
                poll_votes = Vote.select().where(Vote.poll == poll).count()
                total_votes += poll_votes
                
                polls_stats.append({
                    "poll_id": poll.id,
                    "poll_title": poll.title,
                    "votes_count": poll_votes,
                    "candidates_count": poll.candidates.count()
                })
            
            return {
                "election_id": election.id,
                "election_title": election.title,
                "total_polls": total_polls,
                "total_votes": total_votes,
                "total_unique_voters": total_voters,
                "polls": polls_stats
            }
            
        except Election.DoesNotExist:
            raise HTTPException(status_code=404, detail="Избирательная кампания не найдена")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)