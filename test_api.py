import requests
import json
from datetime import datetime, timedelta

# Базовый URL API
BASE_URL = "http://localhost:8000"

def print_response(response, test_name):
    """Вспомогательная функция для вывода результатов теста"""
    print(f"\n{'='*50}")
    print(f"Тест: {test_name}")
    print(f"Статус: {response.status_code}")
    if response.status_code != 200:
        print(f"Ошибка: {response.text}")
    else:
        print("Успех!")
        print(f"Ответ: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print(f"{'='*50}")

def test_health_check():
    """Тест проверки здоровья API"""
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "Health Check")

def test_root():
    """Тест корневого эндпоинта"""
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "Root Endpoint")

def test_elections_crud():
    """Тест CRUD операций для избирательных кампаний"""
    
    # Данные для создания кампании
    election_data = {
        "title": "Тестовая кампания API",
        "description": "Кампания создана через API тестирование",
        "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=10)).isoformat(),
        "is_active": True
    }
    
    # CREATE - Создание кампании
    response = requests.post(f"{BASE_URL}/elections/", json=election_data)
    print_response(response, "CREATE Election")
    
    if response.status_code == 201:
        election_id = response.json()["id"]
        
        # READ - Получение кампании по ID
        response = requests.get(f"{BASE_URL}/elections/{election_id}")
        print_response(response, "READ Election by ID")
        
        # UPDATE - Обновление кампании
        update_data = election_data.copy()
        update_data["title"] = "Обновленная тестовая кампания"
        response = requests.put(f"{BASE_URL}/elections/{election_id}", json=update_data)
        print_response(response, "UPDATE Election")
        
        # LIST - Получение списка кампаний
        response = requests.get(f"{BASE_URL}/elections/")
        print_response(response, "LIST Elections")
        
        return election_id
    return None

def test_polls_crud(election_id):
    """Тест CRUD операций для голосований"""
    
    if not election_id:
        print("Нет election_id для теста голосований")
        return None
    
    poll_data = {
        "election_id": election_id,
        "title": "Тестовое голосование API",
        "description": "Голосование создано через API тестирование",
        "max_votes_per_voter": 1,
        "is_active": True
    }
    
    # CREATE - Создание голосования
    response = requests.post(f"{BASE_URL}/polls/", json=poll_data)
    print_response(response, "CREATE Poll")
    
    if response.status_code == 201:
        poll_id = response.json()["id"]
        
        # READ - Получение голосования по ID
        response = requests.get(f"{BASE_URL}/polls/{poll_id}")
        print_response(response, "READ Poll by ID")
        
        # LIST - Получение списка голосований
        response = requests.get(f"{BASE_URL}/polls/")
        print_response(response, "LIST Polls")
        
        return poll_id
    return None

def test_candidates_crud(poll_id):
    """Тест CRUD операций для кандидатов"""
    
    if not poll_id:
        print("Нет poll_id для теста кандидатов")
        return None
    
    candidate_data = {
        "poll_id": poll_id,
        "name": "Тестовый кандидат API",
        "description": "Кандидат создан через API тестирование"
    }
    
    # CREATE - Создание кандидата
    response = requests.post(f"{BASE_URL}/candidates/", json=candidate_data)
    print_response(response, "CREATE Candidate")
    
    if response.status_code == 201:
        candidate_id = response.json()["id"]
        
        # READ - Получение кандидата по ID
        response = requests.get(f"{BASE_URL}/candidates/{candidate_id}")
        print_response(response, "READ Candidate by ID")
        
        # LIST - Получение списка кандидатов
        response = requests.get(f"{BASE_URL}/candidates/")
        print_response(response, "LIST Candidates")
        
        return candidate_id
    return None

def test_voters_crud():
    """Тест CRUD операций для избирателей"""
    
    voter_data = {
        "email": f"test_{datetime.now().strftime('%H%M%S')}@university.edu",
        "name": "Тестовый избиратель API",
        "is_verified": True
    }
    
    # CREATE - Создание избирателя
    response = requests.post(f"{BASE_URL}/voters/", json=voter_data)
    print_response(response, "CREATE Voter")
    
    if response.status_code == 201:
        voter_id = response.json()["id"]
        
        # READ - Получение избирателя по ID
        response = requests.get(f"{BASE_URL}/voters/{voter_id}")
        print_response(response, "READ Voter by ID")
        
        # LIST - Получение списка избирателей
        response = requests.get(f"{BASE_URL}/voters/")
        print_response(response, "LIST Voters")
        
        return voter_id
    return None

def test_voting_process(poll_id, candidate_id, voter_id):
    """Тест процесса голосования"""
    
    if not all([poll_id, candidate_id, voter_id]):
        print("Недостаточно данных для теста голосования")
        return
    
    vote_data = {
        "poll_id": poll_id,
        "candidate_id": candidate_id,
        "voter_id": voter_id
    }
    
    # CREATE - Голосование
    response = requests.post(f"{BASE_URL}/votes/", json=vote_data)
    print_response(response, "CREATE Vote")
    
    if response.status_code == 201:
        # LIST - Получение списка голосов
        response = requests.get(f"{BASE_URL}/votes/")
        print_response(response, "LIST Votes")

def test_results_and_stats(election_id, poll_id):
    """Тест получения результатов и статистики"""
    
    if election_id:
        # Статистика по кампании
        response = requests.get(f"{BASE_URL}/elections/{election_id}/stats")
        print_response(response, "Election Stats")
    
    if poll_id:
        # Результаты голосования
        response = requests.get(f"{BASE_URL}/polls/{poll_id}/results")
        print_response(response, "Poll Results")

def test_error_cases():
    """Тест обработки ошибок"""
    
    print("\n🔴 ТЕСТИРОВАНИЕ ОШИБОК:")
    
    # Попытка создать кампанию с некорректными датами
    bad_election_data = {
        "title": "Некорректная кампания",
        "start_date": (datetime.now() + timedelta(days=10)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=1)).isoformat(),  # Дата окончания раньше начала
        "is_active": True
    }
    response = requests.post(f"{BASE_URL}/elections/", json=bad_election_data)
    print_response(response, "Error: Incorrect Dates")
    
    # Попытка создать избирателя с существующим email
    duplicate_voter_data = {
        "email": "student1@university.edu",  # Email из тестовых данных
        "name": "Дубликат избирателя",
        "is_verified": True
    }
    response = requests.post(f"{BASE_URL}/voters/", json=duplicate_voter_data)
    print_response(response, "Error: Duplicate Email")
    
    # Попытка получить несуществующую запись
    response = requests.get(f"{BASE_URL}/elections/9999")
    print_response(response, "Error: Non-existent Election")

def test_existing_data():
    """Тест работы с существующими данными"""
    
    print("\n📊 ТЕСТИРОВАНИЕ СУЩЕСТВУЮЩИХ ДАННЫХ:")
    
    # Получение существующих кампаний
    response = requests.get(f"{BASE_URL}/elections/")
    if response.status_code == 200:
        elections = response.json()
        print(f"Найдено кампаний: {len(elections)}")
        
        for election in elections[:2]:  # Тестируем первые 2 кампании
            election_id = election["id"]
            
            # Статистика кампании
            response = requests.get(f"{BASE_URL}/elections/{election_id}/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"Кампания '{election['title']}': {stats['total_votes']} голосов")
            
            # Голосования кампании
            response = requests.get(f"{BASE_URL}/elections/{election_id}")
            if response.status_code == 200:
                election_data = response.json()
                print(f"Голосований в кампании: {len(election_data.get('polls', []))}")

def run_all_tests():
    """Запуск всех тестов"""
    
    print("🚀 ЗАПУСК API ТЕСТИРОВАНИЯ")
    print(f"Базовая ссылка: {BASE_URL}")
    
    try:
        # Базовые тесты
        test_health_check()
        test_root()
        
        # CRUD тесты
        election_id = test_elections_crud()
        poll_id = test_polls_crud(election_id)
        candidate_id = test_candidates_crud(poll_id)
        voter_id = test_voters_crud()
        
        # Тест голосования
        test_voting_process(poll_id, candidate_id, voter_id)
        
        # Тест результатов
        test_results_and_stats(election_id, poll_id)
        
        # Тест ошибок
        test_error_cases()
        
        # Тест существующих данных
        test_existing_data()
        
        print("\n✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ОШИБКА: Не удается подключиться к серверу")
        print("Убедитесь, что сервер запущен на http://localhost:8000")
    except Exception as e:
        print(f"\n❌ НЕОЖИДАННАЯ ОШИБКА: {e}")

if __name__ == "__main__":
    run_all_tests()