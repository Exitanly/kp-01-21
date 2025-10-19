import unittest
import os
import sys
from datetime import datetime, timedelta

# Добавляем путь к проекту для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Election, Poll, Candidate, Voter, Vote, database, create_tables
from schemas import (
    ElectionCreate, PollCreate, CandidateCreate, VoterCreate, VoteCreate,
    ElectionResponse, PollResponse, CandidateResponse, VoterResponse, VoteResponse
)

class TestDatabaseSetup(unittest.TestCase):
    """Тесты настройки базы данных"""
    
    @classmethod
    def setUpClass(cls):
        """Настройка перед всеми тестами"""
        # Используем тестовую базу данных
        database.init('test_voting_system.db')
        create_tables()
    
    @classmethod
    def tearDownClass(cls):
        """Очистка после всех тестов"""
        if not database.is_closed():
            database.close()
        # Удаляем тестовую базу данных
        if os.path.exists('test_voting_system.db'):
            os.remove('test_voting_system.db')
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Очищаем данные перед каждым тестом
        Vote.delete().execute()
        Candidate.delete().execute()
        Poll.delete().execute()
        Election.delete().execute()
        Voter.delete().execute()

class TestModels(TestDatabaseSetup):
    """Тесты моделей базы данных"""
    
    def test_election_creation(self):
        """Тест создания избирательной кампании"""
        election = Election.create(
            title="Тестовая кампания",
            description="Описание тестовой кампании",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            is_active=True
        )
        
        self.assertIsNotNone(election.id)
        self.assertEqual(election.title, "Тестовая кампания")
        self.assertTrue(election.is_active)
    
    def test_poll_creation(self):
        """Тест создания голосования"""
        election = Election.create(
            title="Кампания для голосования",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        poll = Poll.create(
            election=election,
            title="Тестовое голосование",
            max_votes_per_voter=1,
            is_active=True
        )
        
        self.assertIsNotNone(poll.id)
        self.assertEqual(poll.title, "Тестовое голосование")
        self.assertEqual(poll.election, election)
    
    def test_candidate_creation(self):
        """Тест создания кандидата"""
        election = Election.create(
            title="Кампания",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        poll = Poll.create(
            election=election,
            title="Голосование"
        )
        
        candidate = Candidate.create(
            poll=poll,
            name="Тестовый кандидат",
            description="Описание кандидата"
        )
        
        self.assertIsNotNone(candidate.id)
        self.assertEqual(candidate.name, "Тестовый кандидат")
        self.assertEqual(candidate.poll, poll)
    
    def test_voter_creation(self):
        """Тест создания избирателя"""
        voter = Voter.create(
            email="test@university.edu",
            name="Тестовый избиратель",
            is_verified=True
        )
        
        self.assertIsNotNone(voter.id)
        self.assertEqual(voter.email, "test@university.edu")
        self.assertTrue(voter.is_verified)
    
    def test_vote_creation(self):
        """Тест создания голоса"""
        # Создаем все необходимые сущности
        election = Election.create(
            title="Кампания",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        poll = Poll.create(
            election=election,
            title="Голосование"
        )
        
        candidate = Candidate.create(
            poll=poll,
            name="Кандидат"
        )
        
        voter = Voter.create(
            email="voter@university.edu",
            name="Избиратель"
        )
        
        vote = Vote.create(
            poll=poll,
            candidate=candidate,
            voter=voter
        )
        
        self.assertIsNotNone(vote.id)
        self.assertEqual(vote.poll, poll)
        self.assertEqual(vote.candidate, candidate)
        self.assertEqual(vote.voter, voter)
    
    def test_unique_voter_per_poll(self):
        """Тест уникальности голосования избирателя в одном голосовании"""
        election = Election.create(
            title="Кампания",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        poll = Poll.create(election=election, title="Голосование")
        candidate1 = Candidate.create(poll=poll, name="Кандидат 1")
        candidate2 = Candidate.create(poll=poll, name="Кандидат 2")
        voter = Voter.create(email="voter@university.edu", name="Избиратель")
        
        # Первое голосование - должно быть успешно
        vote1 = Vote.create(poll=poll, candidate=candidate1, voter=voter)
        self.assertIsNotNone(vote1.id)
        
        # Попытка второго голосования - должно вызвать ошибку
        with self.assertRaises(Exception):  # Peewee выдаст IntegrityError
            Vote.create(poll=poll, candidate=candidate2, voter=voter)
    
    def test_relationships(self):
        """Тест связей между моделями"""
        election = Election.create(
            title="Кампания",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        poll1 = Poll.create(election=election, title="Голосование 1")
        poll2 = Poll.create(election=election, title="Голосование 2")
        
        candidate1 = Candidate.create(poll=poll1, name="Кандидат 1")
        candidate2 = Candidate.create(poll=poll1, name="Кандидат 2")
        
        voter = Voter.create(email="voter@university.edu", name="Избиратель")
        
        # Проверяем связи
        self.assertEqual(poll1.election, election)
        self.assertEqual(candidate1.poll, poll1)
        self.assertIn(poll1, election.polls)
        self.assertIn(candidate1, poll1.candidates)
    
    def test_cascade_delete(self):
        """Тест каскадного удаления"""
        election = Election.create(
            title="Кампания",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        poll = Poll.create(election=election, title="Голосование")
        candidate = Candidate.create(poll=poll, name="Кандидат")
        
        # Удаляем голосование - кандидат должен удалиться каскадно
        poll_id = poll.id
        candidate_id = candidate.id
        
        poll.delete_instance()
        
        # Проверяем что кандидат удален
        with self.assertRaises(Candidate.DoesNotExist):
            Candidate.get(Candidate.id == candidate_id)

class TestSchemas(TestDatabaseSetup):
    """Тесты Pydantic схем"""
    
    def test_election_schema_validation(self):
        """Тест валидации схемы избирательной кампании"""
        # Корректные данные
        valid_data = {
            "title": "Тестовая кампания",
            "description": "Описание",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=7),
            "is_active": True
        }
        
        election = ElectionCreate(**valid_data)
        self.assertEqual(election.title, "Тестовая кампания")
        self.assertTrue(election.is_active)
    
    def test_election_schema_invalid_dates(self):
        """Тест валидации некорректных дат"""
        invalid_data = {
            "title": "Тестовая кампания",
            "start_date": datetime.now() + timedelta(days=7),
            "end_date": datetime.now(),  # Дата окончания раньше начала
            "is_active": True
        }
        
        # Схема должна принять данные (валидация дат в бизнес-логике)
        election = ElectionCreate(**invalid_data)
        self.assertEqual(election.title, "Тестовая кампания")
    
    def test_poll_schema(self):
        """Тест схемы голосования"""
        poll_data = {
            "election_id": 1,
            "title": "Тестовое голосование",
            "description": "Описание голосования",
            "max_votes_per_voter": 3,
            "is_active": True
        }
        
        poll = PollCreate(**poll_data)
        self.assertEqual(poll.title, "Тестовое голосование")
        self.assertEqual(poll.max_votes_per_voter, 3)
    
    def test_candidate_schema(self):
        """Тест схемы кандидата"""
        candidate_data = {
            "poll_id": 1,
            "name": "Тестовый кандидат",
            "description": "Описание кандидата"
        }
        
        candidate = CandidateCreate(**candidate_data)
        self.assertEqual(candidate.name, "Тестовый кандидат")
    
    def test_voter_schema(self):
        """Тест схемы избирателя"""
        voter_data = {
            "email": "test@university.edu",
            "name": "Тестовый избиратель",
            "is_verified": True
        }
        
        voter = VoterCreate(**voter_data)
        self.assertEqual(voter.email, "test@university.edu")
        self.assertTrue(voter.is_verified)
    
    def test_vote_schema(self):
        """Тест схемы голоса"""
        vote_data = {
            "poll_id": 1,
            "candidate_id": 1,
            "voter_id": 1
        }
        
        vote = VoteCreate(**vote_data)
        self.assertEqual(vote.poll_id, 1)
        self.assertEqual(vote.candidate_id, 1)

class TestBusinessLogic(TestDatabaseSetup):
    """Тесты бизнес-логики"""
    
    def test_vote_validation(self):
        """Тест валидации голосования"""
        election = Election.create(
            title="Кампания",
            start_date=datetime.now() - timedelta(days=1),  # Началась вчера
            end_date=datetime.now() + timedelta(days=6),    # Заканчивается через 6 дней
            is_active=True
        )
        
        poll = Poll.create(
            election=election,
            title="Голосование",
            is_active=True
        )
        
        candidate = Candidate.create(poll=poll, name="Кандидат")
        voter = Voter.create(email="voter@university.edu", name="Избиратель", is_verified=True)
        
        # Голосование должно быть успешным
        vote = Vote.create(poll=poll, candidate=candidate, voter=voter)
        self.assertIsNotNone(vote.id)
    
    def test_inactive_poll_voting(self):
        """Тест голосования в неактивном голосовании"""
        election = Election.create(
            title="Кампания",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        poll = Poll.create(
            election=election,
            title="Неактивное голосование",
            is_active=False  # Голосование неактивно
        )
        
        candidate = Candidate.create(poll=poll, name="Кандидат")
        voter = Voter.create(email="voter@university.edu", name="Избиратель")
        
        # Попытка голосования в неактивном голосовании
        # Это должна обработать бизнес-логика, не модель
        vote = Vote.create(poll=poll, candidate=candidate, voter=voter)
        self.assertIsNotNone(vote.id)  # Модель позволяет, бизнес-логика должна проверять
    
    def test_unverified_voter(self):
        """Тест голосования неверифицированным избирателем"""
        election = Election.create(
            title="Кампания",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        poll = Poll.create(election=election, title="Голосование")
        candidate = Candidate.create(poll=poll, name="Кандидат")
        voter = Voter.create(
            email="unverified@university.edu", 
            name="Неверифицированный избиратель",
            is_verified=False  # Не верифицирован
        )
        
        # Голосование неверифицированным избирателем
        # Модель позволяет, бизнес-логика должна проверять
        vote = Vote.create(poll=poll, candidate=candidate, voter=voter)
        self.assertIsNotNone(vote.id)

class TestQueryMethods(TestDatabaseSetup):
    """Тесты методов запросов"""
    
    def setUp(self):
        super().setUp()
        # Создаем тестовые данные
        self.election = Election.create(
            title="Тестовая кампания",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        self.poll = Poll.create(election=self.election, title="Тестовое голосование")
        
        self.candidates = [
            Candidate.create(poll=self.poll, name=f"Кандидат {i}") 
            for i in range(1, 4)
        ]
        
        self.voters = [
            Voter.create(email=f"voter{i}@university.edu", name=f"Избиратель {i}")
            for i in range(1, 6)
        ]
    
    def test_vote_counting(self):
        """Тест подсчета голосов"""
        # Создаем голоса
        Vote.create(poll=self.poll, candidate=self.candidates[0], voter=self.voters[0])
        Vote.create(poll=self.poll, candidate=self.candidates[0], voter=self.voters[1])
        Vote.create(poll=self.poll, candidate=self.candidates[1], voter=self.voters[2])
        
        # Подсчитываем голоса для каждого кандидата
        votes_candidate1 = Vote.select().where(Vote.candidate == self.candidates[0]).count()
        votes_candidate2 = Vote.select().where(Vote.candidate == self.candidates[1]).count()
        votes_candidate3 = Vote.select().where(Vote.candidate == self.candidates[2]).count()
        
        self.assertEqual(votes_candidate1, 2)
        self.assertEqual(votes_candidate2, 1)
        self.assertEqual(votes_candidate3, 0)
    
    def test_active_elections_query(self):
        """Тест запроса активных кампаний"""
        # Создаем еще одну неактивную кампанию
        inactive_election = Election.create(
            title="Неактивная кампания",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            is_active=False
        )
        
        active_elections = Election.select().where(Election.is_active == True)
        self.assertEqual(active_elections.count(), 1)
        self.assertEqual(active_elections[0].title, "Тестовая кампания")
    
    def test_voter_participation(self):
        """Тест участия избирателей в голосованиях"""
        # Избиратель 1 голосует
        Vote.create(poll=self.poll, candidate=self.candidates[0], voter=self.voters[0])
        
        # Избиратель 2 голосует дважды (в разных голосованиях)
        poll2 = Poll.create(election=self.election, title="Другое голосование")
        candidate2 = Candidate.create(poll=poll2, name="Кандидат другого голосования")
        
        Vote.create(poll=self.poll, candidate=self.candidates[1], voter=self.voters[1])
        Vote.create(poll=poll2, candidate=candidate2, voter=self.voters[1])
        
        # Подсчитываем участие
        votes_voter1 = Vote.select().where(Vote.voter == self.voters[0]).count()
        votes_voter2 = Vote.select().where(Vote.voter == self.voters[1]).count()
        votes_voter3 = Vote.select().where(Vote.voter == self.voters[2]).count()
        
        self.assertEqual(votes_voter1, 1)
        self.assertEqual(votes_voter2, 2)
        self.assertEqual(votes_voter3, 0)

class TestEdgeCases(TestDatabaseSetup):
    """Тесты граничных случаев"""
    
    def test_empty_database(self):
        """Тест работы с пустой базой данных"""
        self.assertEqual(Election.select().count(), 0)
        self.assertEqual(Poll.select().count(), 0)
        self.assertEqual(Candidate.select().count(), 0)
        self.assertEqual(Voter.select().count(), 0)
        self.assertEqual(Vote.select().count(), 0)
    
    def test_long_text_fields(self):
        """Тест длинных текстовых полей"""
        long_title = "О" * 200  # Максимальная длина для CharField
        election = Election.create(
            title=long_title,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        self.assertEqual(election.title, long_title)
    
    def test_special_characters(self):
        """Тест специальных символов в данных"""
        special_text = "Тест с спецсимволами: !@#$%^&*()_+{}[]:;'<>,.?/~`"
        voter = Voter.create(
            email="special@university.edu",
            name=special_text
        )
        
        self.assertEqual(voter.name, special_text)

def run_tests():
    """Запуск всех тестов"""
    # Загружаем тесты из текущего модуля
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Возвращаем результат для CI/CD
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🚀 ЗАПУСК UNIT ТЕСТОВ")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        sys.exit(0)
    else:
        print("\n❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
        sys.exit(1)