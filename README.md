# Телеграм Бот
______________

Введение
- [Телеграм Бот](#телеграм-бот)
  - [Архитектура проекта (aiogram 3.18.0 + Motor)](#архитектура-проекта-aiogram-3180--motor)
      - [1. **Слой обработки запросов (Handlers)**](#1-слой-обработки-запросов-handlers)
      - [2. **Бизнес-логика (Services)**](#2-бизнес-логика-services)
      - [3. **Работа с данными (Repositories \& Models)**](#3-работа-с-данными-repositories--models)
      - [4. **Конфигурация и утилиты**](#4-конфигурация-и-утилиты)
      - [5. **Запуск и инфраструктура**](#5-запуск-и-инфраструктура)
    - [Зависимости](#зависимости)
    - [Схема взаимодействия](#схема-взаимодействия)
  - [Развертывание](#развертывание)
    - [Нативно](#Нативно)
    - [В докере](#в-докере)
  - [Запуск в PROXMOX](#запуск-proxmox-)
  - [Развертывание PROD](#развертывание-prod)
  - [Дополнительно](#дополнительно)
    - [DockerCompose](#dockercompose)
    - [Посмотреть логи](#посмотреть-логи)
    - [Подключение к консоли контейнера](#подключение-к-консоли-контейнера)
    - [Посмотреть состояние контейнеров](#посмотреть-состояние-контейнеров)
    - [Отладка в runtime](#отладка-в-runtime)
  - [Подключиться к БД](#подключиться-к-бд)

## Архитектура проекта (aiogram 3.18.0 + Motor)

[Doc](https://docs.aiogram.dev/en/v3.18.0/index.html)

Проект структурирован с использованием слоёв (Handler → Service → Repository → Model)
Основные компоненты:

---

#### 1. **Слой обработки запросов (Handlers)**
state сохраняется в mongo. Работ происходит с помощью FSMContext в котором определены методы использующие storage   
storage это класс наследник от BaseStorage - это абстрактный клас. MongoStorage, RadisStorage наследуется от BaseStorage.
Соответственно при необходимости, можно расширить список запросов написав свой Storage и FSMContext
 

- **`handlers/`**: Обработчики Telegram-бота (на основе aiogram).
    - `auth.py` — аутентификация/авторизация выполняется после команды `/start`, когда пользователь в первые нажал на `Предоставить номер телефона`
    - `help.py` — справка (`/help`, FAQ). В разработке 
    - `monitoring.py` — мониторинг `/monitoring` отображает список устройств/сайтов их добавление, редактирование, удаление.
    - `settings.py` — настройки пользователя `/settings`. В разработке
    - `start.py` — команды `/start`.
---

#### 2. **Бизнес-логика (Services)**
device_monitor_service - запускается периодические (не зависимо от fsm)
Выполняет запрос в бд, который возвращает c список девайсов пользователей {"all_ips": [], "all_services": []}
Асинхронно проходит по всем ips(ping) и services(http) 

- **`services/`**: Сервисы для выполнения бизнес-задач.
    - `device_monitor_service.py` — управление мониторингом устройств (проверка статуса, уведомления).
    - **Использует**: Репозитории для доступа к данным `repositories/user_repo.py`. 

---

#### 3. **Работа с данными (Repositories & Models)**
- **`models/`**: Модели данных (Pydantic/SQLAlchemy).
    - `user.py` — модель пользователя (поля: `id`, `email`, `hashed_password`, `devices`).

- **`repositories/`**: Репозитории для взаимодействия с БД.
    - `user_repo.py` — CRUD для пользователей.  
      **Драйверы**:
        -  `motor` (MongoDB) — в зависимости от конфига.

---

#### 4. **Конфигурация и утилиты**
- **`config/settings.py`**: Настройки приложения через `.env` (использует `pydantic_settings`).
- **`utils/`**: Вспомогательные модули:
    - [keyboards.py](src/utils/keyboards.py) - Кнопки, которые используются в `handlers/`

---

#### 5. **Запуск и инфраструктура**
- **`main.py`**: Точка входа — запуск бота и настройка диспетчера.
- **Docker**:
    - `Dockerfile` — сборка образа с Python + зависимостями.
    - `docker-compose.yml` — развертывание бота + /MongoDB.
- **Тесты**:
    - `tests/` — модульные тесты (используют `pytest`).

---

### Зависимости
- **Асинхронность**: `aiogram`.
- **Базы данных**:
    - MongoDB (`motor`).
- **Валидация**: `pydantic` + `validators`.
- **Конфиги**: `python-dotenv` + `pydantic-settings`.

---

### Схема взаимодействия
```
Main start the app
Telegram User -> Handler → Database  
                 ↓
                Utils
            
```


## Развертывание
### Прокси
Прокси которые используются в главе [Настройка в ProxMox](#настройка-в-proxmox)

По умолчанию без пароля, доступ к ним по Ip.

Доступы сконфигурированные у 2 машин: 138.145 и 138.251 

Для получения доступа нужно обращаться к DevOps

### Нативно

Проверялось в нативной Ubuntu 22.04

```bash
git clone git@gitlab.dmz:neuron/neuron/neuron_tg_bot.git
cd neuron_tg_bot
# запустите в докере окружение для программы
docker-compose up mongodb -d
```
 Запустите саму программу для работы бота:
```bash
# Эта команда создаст директорию с именем `tg`, содержащую виртуальную среду.
python3 -m venv tg
# примените созданное окружение
source tg/bin/activate
# Установка зависимостей
pip install -r requirements.txt
# при необходимости обновите настройки в файле [exemple.env](/.env)
python src/main.py
```

### В докере

Проверялось в нативной Win10, Ubuntu 22.04

```bash
git clone git@gitlab.dmz:neuron/neuron/neuron_tg_bot.git
cd neuron_tg_bot
# при необходимости обновите настройки в файле [exemple.env](/.env)
.env определяет окружение настройки [exemple.env](/.env)
# запуск приложения и окружения в текущем терминале
docker compose --env-file your_file.env up --build 
# запуск программы и окружения как демон
docker compose --env-file your_file.env up --build  -d
```

Бот запустился, можно идти в ТГ
```
INFO:aiogram.dispatcher:Start polling
INFO:aiogram.dispatcher:Run polling for bot @neuron_test_bot id=8098108582 - 'Neuron'
```

### Настройка в PROXMOX

#### подключить интернет на витуальной машине в proxmox в dmz
```bash
# определить DMZ DNS на виртуальной машине
echo nameserver 172.16.254.2 >> /etc/resolv.conf
# Подключение прокси
export http_proxy=http://172.16.254.1:3128
export https_proxy=http://172.16.254.1:3128
export HTTP_PROXY=http://172.16.254.1:3128
export HTTPS_PROXY=http://172.16.254.1:3128
```

#### Установка docker и docker-compose

```bash
wget ftp://172.16.254.9/jenkins/NEURON/repo-4/docker/docker-ce_28.0.0-1~debian.11~bullseye_amd64.deb
wget ftp://172.16.254.9/jenkins/NEURON/repo-4/docker/docker-ce-cli_28.0.0-1~debian.11~bullseye_amd64.deb
wget ftp://172.16.254.9/jenkins/NEURON/repo-4/docker/containerd.io_1.7.25-1_amd64.deb
wget ftp://172.16.254.9/jenkins/NEURON/repo-4/docker/docker-compose-plugin_2.33.0-1~debian.11~bullseye_amd64.deb

dpkg -i  docker-ce_28.0.0-1~debian.11~bullseye_amd64.deb docker-ce-cli_28.0.0-1~debian.11~bullseye_amd64.deb containerd.io_1.7.25-1_amd64.deb docker-compose-plugin_2.33.0-1~debian.11~bullseye_amd64.deb

# При обработке следующих пакетов произошли ошибки:
#  containerd.io
#  docker-ce
# это ок


# убедитесь, что память есть
df -h

Файловая система Размер Использовано  Дост Использовано% Cмонтировано в
udev               2,0G            0  2,0G            0% /dev
tmpfs              395M          47M  349M           12% /run
/dev/sda1           28G          26G  935M           97% /
tmpfs              2,0G            0  2,0G            0% /dev/shm
tmpfs              5,0M            0  5,0M            0% /run/lock
tmpfs              2,0G            0  2,0G            0% /sys/fs/cgroup
tmpfs              395M            0  395M            0% /run/user/999
tmpfs              395M            0  395M            0% /run/user/1000

# настраиваем прокси для докера 
mkdir -p /etc/systemd/system/docker.service.d
nano /etc/systemd/system/docker.service.d/http-proxy.conf

[Service]
Environment="HTTP_PROXY=http://172.16.254.1:3128"
Environment="HTTPS_PROXY=http://172.16.254.1:3128"
Environment="NO_PROXY="

# Пробуем запустить 
sudo groupadd docker
sudo usermod -aG docker $USER
sudo systemctl enable docker.service
sudo systemctl enable containerd.service

# Если выдает ошибку 
# Седелайте systemctl unmask

# В случае, когда runc устарел 
wget ftp://172.16.254.9/jenkins/NEURON/repo-4/docker/libseccomp2_2.5.5-2_amd64.deb
dpkg -i libseccomp2_2.5.5-2_amd64.deb
wget ftp://172.16.254.9/jenkins/NEURON/repo-4/docker/runc_1.1.15+ds1-2_amd64.deb
dpkg -i runc_1.1.15+ds1-2_amd64.deb
```

Еще один варианты настройки проски для docker
~/.docker/config.json
```
  {
    "proxies": {
      "default": {
        "httpProxy": "http://172.16.254.1:3128",
        "httpsProxy": "http://172.16.254.1:3128",
        "noProxy": "registry-1.docker.com,*.docker.com,repos2.dmz:8082"
    }
  }
}
```
> Источники
>
> astra 1.7/6 https://micronode.ru/domestic/astra_linux/1.7/docker
>
> proxy for docker - https://docs.docker.com/engine/daemon/proxy/  https://docs.docker.com/engine/cli/proxy/


#### Запуск PROXMOX 

```bash
#add to .env
http_proxy=http://172.16.254.1:3128
https_proxy=http://172.16.254.1:3128
HTTP_PROXY=http://172.16.254.1:3128
HTTPS_PROXY=http://172.16.254.1:3128


docker compose -f docker-compose.proxmox.yml  up --build -d
```

### Развертывание PROD

### Запуск на машине
```bash
# При первой установке
wget ftp://172.16.254.9/jenkins/NEURON/repo-4/tg_bot/mongo_lasted_24_02_2025.tar
docker load -i mongo_lasted_24_02_2025.tar
docker tag 6551ff2e441b mongo:latest-24-02-2025

docker compose -f docker-compose.prod.yml --env-file prod.env up --build -d

# При новом релизе
# unarhive tag zip
cd old_tag_name
docker compose -f docker-compose.prod.yml down 
cd ..
mkdir new_tag_name/data
getent group | grep docker
sudo chown username:groupname data
sudo cp -R tg_bot_0_0_6/data/* tg_bot_0_0_7/data
docker compose -f docker-compose.prod.yml --env-file prod.env up --build -d
```

#### Изменить настройки для бота при необходимости

> Необходимо создать новый файл .env (пример [exemple.env](/.env))




## Дополнительно
### DockerCompose

    Команда `docker-compose` - это старая версия, лучше использовать `docker compose` 

#### Посмотреть логи

По умолчанию логи Docker Compose хранятся внутри каждого контейнера в виде файлов JSON, расположенных в 
директории /var/lib/docker/containers/<container_id>/. 
Формат и ротация логов зависят от настроенного драйвера логирования

Вывод логов всех сервисов
```commandline
docker-compose logs 
docker-compose logs -f
```
Флаг `-f` в команде `docker-compose logs -f` используется для того, 
чтобы следить за логами контейнеров в реальном времени. 
Это означает, что команда будет выводить новые записи логов по мере их появления,
аналогично команде `tail -f` в Unix-подобных системах.

Логи конкретного сервиса.

```commandline
docker-compose logs <service>
```

Логи конкретного сервиса.
```commandline
docker-compose logs --tail=100 --follow 
```
#### Подключение к консоли контейнера
```commandline
docker exec -it tg_boot /bin/bash
```
#### Посмотреть состояние контейнеров

Чтобы проверить состояние контейнеров, управляемых Docker Compose, вы можете использовать команду `docker-compose ps`. 
Эта команда выводит список всех контейнеров, связанных с вашим проектом Docker Compose,
и их текущий статус.

```bash
docker-compose ps
```

Эта команда покажет вам таблицу, содержащую информацию о каждом контейнере, включая:

- Имя контейнера
- Команду, которая была использована для запуска контейнера
- Состояние контейнера (например, `Up` для работающего контейнера или `Exited` для остановленного)
- Порты, которые были опубликованы

Если вы хотите получить более подробную информацию о конкретном контейнере, 
вы можете использовать команду `docker inspect` вместе с идентификатором контейнера. Например:

```bash
docker inspect <container_id>
```

Эта команда выведет подробную информацию о контейнере в формате JSON, 
включая его конфигурацию, состояние, сетевые настройки и многое другое.

### Отладка в runtime

На данный момент такой возможности нет. Необходимо реализовать поддержку в коде для этого.

#### Подключиться к БД

Для подключения к запущенное в докере MongoDB, выполните следующие шаги:

```bash
$ docker exec -it mongodb /bin/bash
docker:/mongosh
test>show dbs 
test>use neurone_tg_bot
db>show collections
```

#### Сохранение образа в архив

```bash
#  Сохранить образ в tar
docker build .
docker image ls
docker save -o tg_bot_0_0_5.tar image_id
```
