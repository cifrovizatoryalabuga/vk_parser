# VK Parser

[Техническое задание на разработку](https://docs.google.com/document/d/1mAs3OnKY-gFu6N2Ee3LUhC9JWFG3JbsEcQ1JczuVeH4/edit?usp=sharing)

[Презентация](https://docs.google.com/presentation/d/1TudWUoRVkU7DpJe_U7UJCA-MVX24h9vf3zqGAr5kY-A/edit?usp=sharing)

## Архитектура

### Схема сервисов

![Services](https://www.plantuml.com/plantuml/png/RS-_IWGn4CVnFaynf4_XrSjoWgK7hYBMayiWost-93FHrtU7YxY5pVBRBvzYScR19Zrk1g-I6zXtfcO16Ve-p3N7aXCb0ViOufeiJDC5MQZDioBKU5Iynh8HVDrKVkHs-vNV3qTMi351oIp_qPEfdJg1VKNlLxaiAXPDTr1DG46Fl9ENpFBPw6rvLlHqxyC5Rum-0zmyBaNzWjl_wzzMLs5oJeySusI27qdNQ6TAeSVj1m00)

### Схема БД

![Database](https://www.plantuml.com/plantuml/png/fP9HJiCm38RVUue-8-q2aPXsayYZfZCqQR2T0KBSdNgT0b7Am-2j_NxR-d_71r5WpM7g0gG-0GkoPtp9ADf_T3Jqz_l-I2D5nH6v4mNDOb2KAOuTnPJL3w1Wy4dcs35AdhxPtKeVAPASSF2WArrqL0hO8VFCFg08ZBXgr-4FZA2bfJJaD6pXpqk6yxCVUSvfotsTppVwqjkmp9EHFpggBFaqRs-r53IATRHp5T_qXwbieIxUnIWmm_i_dTh8cvoQOasjmF1QtyUHM4-6riUsZ-KwMDH722kx1flWDtWc8RNCzPYRGzSNuTpYVhVRbpqurvnCMK5LN9xNkVAxKLilkAuzO1nocBu0)

## Стек технологий

- Python 3.11
- Aiohttp
- Aiomisc
- aio-pika
- SQLAlchemy
- Alembic
- msgpack


# Запуск проекта для локальной разработки
Разработку необходимо производить с корпоративного аккаунта AlabugaCifrovizatory
1. Клонируем git к себе на локальную машину. `git clone git@github.com:cifrovizatoryalabuga/vk_parser.git`
2. Устанавливаем версию Python 3.11
3. Открываем терминал и прописываем команды `make develop` после этого запускаем venv окружение командой source .venv/bin/activate.
4. Затем создайте в проекте `.env` файл, и добавьте туда строки:
```
APP_PG_DSN=postgresql+asyncpg://pguser:pguser@127.0.0.1:5432/pgdb
APP_AMQP_DSN=amqp://guest:guest@127.0.0.1:5672/

APP_VK_API_SECURE_KEY=YOUR
APP_VK_API_SERVICE_TOKEN=YOUR
```
P.S. Данные для VK можно взять по ссылке `https://dev.vk.com/ru/reference/roadmap`

Всего нужно будет использовать 3-4 терминала по мере необходимости разработки определенных модулей, 2 обязательных и 2 для создания парсеров.

5. Терминал 1 : Настройте импорт env через команду `set -a && source .env && set +a && make local` для развертывания контейнеров БД и Рэбит.
6. Терминал 2 : Настройте импорт env через команду `set -a && source .env && set +a && python -m vk_parser.db upgrade head && python -m vk_parser.admin` для накатки миграций в бд и старта проекта.
7. Терминал 3 : Настройте импорт env через команду `set -a && source .env && set +a && python -m vk_parser.workers.vk --amqp-queue-name=VK_DOWNLOAD_AND_PARSED_POSTS` для поднятия воркеров. PS для работы с VK_SIMPLE_DOWNLOAD используйте вместо этой команды `python -m vk_parser.workers.vk --amqp-queue-name=VK_SIMPLE_DOWNLOAD` или запустите её в другом терминале.
8. Переходите по ip, вносите изменения изучайте проект.!
