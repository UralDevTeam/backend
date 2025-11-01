-- init-db.sql
-- Выполняется один раз при инициализации кластера Postgres (docker-entrypoint-initdb.d)
-- Требует существующих таблиц из миграций: positions, teams, employees, status_history

BEGIN;
-- Отключаем проверку FK/триггеров в рамках ТЕКУЩЕЙ транзакции
SET LOCAL session_replication_role = 'replica';

-- ===== 1) POSITIONS =====
-- Фиксированные UUID для позиций (можешь поменять на свои)
INSERT INTO positions (id, title) VALUES
  ('11111111-1111-1111-1111-111111111111', 'CEO'),
  ('22222222-2222-2222-2222-222222222222', 'CTO'),
  ('33333333-3333-3333-3333-333333333333', 'Team Lead Backend'),
  ('44444444-4444-4444-4444-444444444444', 'Senior Python Developer'),
  ('55555555-5555-5555-5555-555555555555', 'Middle Python Developer'),
  ('66666666-6666-6666-6666-666666666666', 'Junior Python Developer'),
  ('77777777-7777-7777-7777-777777777777', 'Frontend Team Lead'),
  ('88888888-8888-8888-8888-888888888888', 'Middle Frontend Developer'),
  ('99999999-9999-9999-9999-999999999999', 'QA Engineer'),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'DevOps Engineer')
ON CONFLICT (id) DO NOTHING;

-- ===== 2) TEAMS =====
-- ВАЖНО: leader_employee_id ссылается на будущие employees.* – FK временно отключены, это ок.
-- Фиксированные UUID команд
-- t-руководство, t-backend, t-frontend, t-qa, t-devops
INSERT INTO teams (id, name, parent_id, leader_employee_id) VALUES
  ('aaaaaaaa-bbbb-cccc-dddd-000000000001', 'Руководство', NULL, '550e8400-e29b-41d4-a716-446655440001'), -- CEO
  ('aaaaaaaa-bbbb-cccc-dddd-000000000002', 'Backend',     'aaaaaaaa-bbbb-cccc-dddd-000000000001', '550e8400-e29b-41d4-a716-446655440003'), -- Team Lead Backend
  ('aaaaaaaa-bbbb-cccc-dddd-000000000003', 'Frontend',    'aaaaaaaa-bbbb-cccc-dddd-000000000001', '550e8400-e29b-41d4-a716-446655440007'), -- Frontend TL
  ('aaaaaaaa-bbbb-cccc-dddd-000000000004', 'QA',          'aaaaaaaa-bbbb-cccc-dddd-000000000001', '550e8400-e29b-41d4-a716-446655440009'), -- QA Engineer (тимлида нет — ставим его же)
  ('aaaaaaaa-bbbb-cccc-dddd-000000000005', 'DevOps',      'aaaaaaaa-bbbb-cccc-dddd-000000000001', '550e8400-e29b-41d4-a716-446655440010')  -- DevOps Engineer (тимлида нет — ставим его же)
ON CONFLICT (id) DO NOTHING;

-- ===== 3) EMPLOYEES =====
-- Разбиваем ФИО по колонкам first/middle/last, проставляем осмысленные данные
-- hire_date и прочее — примерные значения, можешь подправить под реальность
INSERT INTO employees (id, first_name, middle_name, last_name, birth_date, hire_date, city, phone, mattermost, about_me, team_id, position_id) VALUES
  ('550e8400-e29b-41d4-a716-446655440001', 'Петр',      'Сергеевич',    'Иванов',   '1975-03-15', '2000-01-01', 'Москва',          '+7-900-000-00-01', 'ivanov.ps', 'Основатель компании, 25 лет опыта в IT',                             'aaaaaaaa-bbbb-cccc-dddd-000000000001', '11111111-1111-1111-1111-111111111111'),
  ('550e8400-e29b-41d4-a716-446655440002', 'Анна',      'Владимировна', 'Смирнова', '1982-07-22', '2009-01-01', 'Москва',          '+7-900-000-00-02', 'smirnova.av','Технический директор, эксперт в системной архитектуре',              'aaaaaaaa-bbbb-cccc-dddd-000000000001', '22222222-2222-2222-2222-222222222222'),
  ('550e8400-e29b-41d4-a716-446655440003', 'Дмитрий',   'Александрович','Кузнецов', '1988-11-08', '2016-01-01', 'Санкт-Петербург', '+7-900-000-00-03', 'kuznetsov.da','Руководитель команды Backend, Python/FastAPI эксперт',               'aaaaaaaa-bbbb-cccc-dddd-000000000002', '33333333-3333-3333-3333-333333333333'),
  ('550e8400-e29b-41d4-a716-446655440004', 'Елена',     'Игоревна',     'Петрова',  '1990-05-12', '2018-01-01', 'Москва',          '+7-900-000-00-04', 'petrova.ei', 'Специализируюсь на микросервисах и API',                              'aaaaaaaa-bbbb-cccc-dddd-000000000002', '44444444-4444-4444-4444-444444444444'),
  ('550e8400-e29b-41d4-a716-446655440005', 'Максим',    'Викторович',   'Соколов',  '1993-09-25', '2020-01-01', 'Казань',          '+7-900-000-00-05', 'sokolov.mv', 'Работаю с Django и FastAPI, увлекаюсь DevOps',                        'aaaaaaaa-bbbb-cccc-dddd-000000000002', '55555555-5555-5555-5555-555555555555'),
  ('550e8400-e29b-41d4-a716-446655440006', 'Дарья',     'Сергеевна',    'Морозова', '1998-01-30', '2023-01-01', 'Новосибирск',     '+7-900-000-00-06', 'morozova.ds','Начинающий разработчик, изучаю Python и SQL',                         'aaaaaaaa-bbbb-cccc-dddd-000000000002', '66666666-6666-6666-6666-666666666666'),
  ('550e8400-e29b-41d4-a716-446655440007', 'Артем',     'Николаевич',   'Волков',   '1987-04-18', '2015-01-01', 'Москва',          '+7-900-000-00-07', 'volkov.an',  'React/TypeScript эксперт, люблю чистый код',                          'aaaaaaaa-bbbb-cccc-dddd-000000000003', '77777777-7777-7777-7777-777777777777'),
  ('550e8400-e29b-41d4-a716-446655440008', 'Ольга',     'Дмитриевна',   'Новикова', '1992-12-05', '2019-01-01', 'Санкт-Петербург', '+7-900-000-00-08', 'novikova.od','Работаю с React и Vue.js, интересуюсь UX',                            'aaaaaaaa-bbbb-cccc-dddd-000000000003', '88888888-8888-8888-8888-888888888888'),
  ('550e8400-e29b-41d4-a716-446655440009', 'Игорь',     'Павлович',     'Лебедев',  '1991-06-14', '2019-01-01', 'Екатеринбург',    '+7-900-000-00-09', 'lebedev.ip', 'Автоматизирую тесты на Pytest, Selenium',                             'aaaaaaaa-bbbb-cccc-dddd-000000000004', '99999999-9999-9999-9999-999999999999'),
  ('550e8400-e29b-41d4-a716-446655440010', 'Сергей',    'Андреевич',    'Федоров',  '1985-08-20', '2012-01-01', 'Москва',          '+7-900-000-00-10', 'fedorov.sa', 'Kubernetes, Docker, CI/CD — моя стихия',                              'aaaaaaaa-bbbb-cccc-dddd-000000000005', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')
ON CONFLICT (id) DO NOTHING;

-- ===== 4) STATUS_HISTORY (минимальные записи статуса) =====
INSERT INTO status_history (id, employee_id, status, started_at, ended_at) VALUES
  ('10000000-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440009', 'active', now(), NULL)
ON CONFLICT (id) DO NOTHING;

-- Возвращаем проверку ограничений в исходное состояние для транзакции
SET LOCAL session_replication_role = 'origin';
COMMIT;
