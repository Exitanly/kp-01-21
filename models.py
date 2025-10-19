from peewee import *
from datetime import datetime

# Настройка подключения к базе данных SQLite
database = SqliteDatabase('voting_system.db', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 64,  # 64MB page-cache
    'foreign_keys': 1,  # Enforce foreign-key constraints
})

class BaseModel(Model):
    """Базовая модель с общими полями"""
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        database = database

class Election(BaseModel):
    """Избирательная кампания"""
    title = CharField(max_length=200, verbose_name='Название кампании')
    description = TextField(null=True, verbose_name='Описание')
    start_date = DateTimeField(verbose_name='Дата начала')
    end_date = DateTimeField(verbose_name='Дата окончания')
    is_active = BooleanField(default=True, verbose_name='Активна')
    
    class Meta:
        table_name = 'elections'
        indexes = (
            (('is_active', 'start_date'), False),
        )
    
    def __str__(self):
        return f"Election {self.id}: {self.title}"

class Poll(BaseModel):
    """Голосование"""
    election = ForeignKeyField(
        Election, 
        backref='polls',
        on_delete='CASCADE',
        verbose_name='Избирательная кампания'
    )
    title = CharField(max_length=200, verbose_name='Название голосования')
    description = TextField(null=True, verbose_name='Описание')
    max_votes_per_voter = IntegerField(default=1, verbose_name='Макс. голосов на избирателя')
    is_active = BooleanField(default=True, verbose_name='Активно')
    
    class Meta:
        table_name = 'polls'
        indexes = (
            (('election', 'is_active'), False),
        )
    
    def __str__(self):
        return f"Poll {self.id}: {self.title}"

class Candidate(BaseModel):
    """Кандидат/Вариант выбора"""
    poll = ForeignKeyField(
        Poll, 
        backref='candidates',
        on_delete='CASCADE',
        verbose_name='Голосование'
    )
    name = CharField(max_length=100, verbose_name='Имя кандидата')
    description = TextField(null=True, verbose_name='Описание')
    
    class Meta:
        table_name = 'candidates'
        indexes = (
            (('poll', 'name'), True),  # Уникальное имя в рамках голосования
        )
    
    def __str__(self):
        return f"Candidate {self.id}: {self.name}"

class Voter(BaseModel):
    """Избиратель"""
    email = CharField(
        max_length=100, 
        unique=True,
        verbose_name='Email',
        index=True
    )
    name = CharField(max_length=100, verbose_name='Имя избирателя')
    is_verified = BooleanField(default=False, verbose_name='Верифицирован')
    
    class Meta:
        table_name = 'voters'
    
    def __str__(self):
        return f"Voter {self.id}: {self.name}"

class Vote(BaseModel):
    """Голос"""
    poll = ForeignKeyField(
        Poll, 
        backref='votes',
        on_delete='CASCADE',
        verbose_name='Голосование'
    )
    candidate = ForeignKeyField(
        Candidate, 
        backref='votes',
        on_delete='CASCADE',
        verbose_name='Кандидат'
    )
    voter = ForeignKeyField(
        Voter, 
        backref='votes',
        on_delete='CASCADE',
        verbose_name='Избиратель'
    )
    voted_at = DateTimeField(default=datetime.now, verbose_name='Время голосования')
    
    class Meta:
        table_name = 'votes'
        indexes = (
            # Один избиратель может голосовать только один раз в каждом голосовании
            (('poll', 'voter'), True),
            # Для быстрого подсчета голосов по кандидатам
            (('candidate', 'poll'), False),
        )
    
    def __str__(self):
        return f"Vote {self.id}: {self.voter.name} -> {self.candidate.name}"

def create_tables():
    """Создание таблиц в базе данных"""
    tables = [Election, Poll, Candidate, Voter, Vote]
    
    try:
        database.connect()
        database.create_tables(tables, safe=True)
        print("✅ Таблицы успешно созданы")
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
    finally:
        if not database.is_closed():
            database.close()

def initialize_database():
    """Инициализация базы данных с тестовыми данными (опционально)"""
    create_tables()
    
    # Добавляем тестовые данные, если таблицы пустые
    if not Election.select().exists():
        from datetime import datetime, timedelta
        
        # Создаем тестовую избирательную кампанию
        election = Election.create(
            title="Выборы студенческого совета 2024",
            description="Ежегодные выборы в студенческий совет университета",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            is_active=True
        )
        
        # Создаем голосование
        poll = Poll.create(
            election=election,
            title="Выборы председателя студенческого совета",
            description="Голосование за кандидатов на пост председателя",
            max_votes_per_voter=1,
            is_active=True
        )
        
        # Создаем кандидатов
        candidates_data = [
            {"name": "Иван Петров", "description": "Факультет информатики, 3 курс"},
            {"name": "Мария Сидорова", "description": "Факультет экономики, 4 курс"},
            {"name": "Алексей Козлов", "description": "Факультет менеджмента, 2 курс"},
        ]
        
        for candidate_data in candidates_data:
            Candidate.create(poll=poll, **candidate_data)
        
        # Создаем тестового избирателя
        voter = Voter.create(
            email="test@university.edu",
            name="Тестовый Избиратель",
            is_verified=True
        )
        
        print("✅ Тестовые данные добавлены")
    
    print("✅ База данных инициализирована")

# Функции для работы с базой данных
def get_db():
    """Получить подключение к базе данных (для использования в контексте)"""
    return database

def close_db():
    """Закрыть подключение к базе данных"""
    if not database.is_closed():
        database.close()

# Контекстный менеджер для работы с БД
class DBContext:
    """Контекстный менеджер для работы с базой данных"""
    def __enter__(self):
        database.connect()
        return database
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not database.is_closed():
            database.close()

if __name__ == "__main__":
    # Инициализация БД при прямом запуске файла
    initialize_database()