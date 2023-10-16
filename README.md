
<!-- ABOUT THE PROJECT -->
## About The Project

Test task from webtronics: "Create a simple RESTful API using FastAPI for a social networking application".



## Built With


* [![Docker][docker.com]][Docker-url]
* [![SqlAlchemy][sqlalchemy.org]][sqlalchemy-url]
* [![PostgreSQL][postgresql.org]][Postgresql-url]
* [![FastApi][fastapi.tiangolo.com]][Fastapi-url]
* [![Pydantic][docs.pydantic.dev]][Pydantic-url]
* [![Python][Python.org]][Python-url]
* [![Pytest][docs.pytest.org]][Pytest-url]
* [![Nginx][nginx.org]][Nginx-url]

<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running, follow these simple example steps.

## Prerequisites

#### 1) There are several customizable fields in the app/settings.py file as follows. You can customize them according to your needs.
```
    DEBUG = False
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_HOURS = 24*3
    CONCURRENT_CONNECTIONS = 0
```
- DEBUG - If the value is False, there will be used the production base connection settings, and server errors will not be displayed in the console. 
If the value is True, there will be used the test base connection settings (make sure that the test base is running), and server errors will be displayed in the console.
- ACCESS_TOKEN_EXPIRE_MINUTES - Specify the lifetime of the authorization token in minutes.
- REFRESH_TOKEN_EXPIRE_HOURS - Specify the lifetime of the refresh token in hours.
CONCURRENT_CONNECTIONS - The number of simultaneous connections to the system by one user. 
If 0 is specified, the number is unlimited. If more than 0 is specified, for example, 4, 
the user can have the specified number of valid authorizations at the same time (as for the example, 4 valid authorizations at the same time), 
and with each new authorization the oldest one will be unavailable.

#### 2) Before starting the server, you must create an .env file with your data in the root directory. Specify PostgreSQL connection settings and specify SECRET_KEY.

```bash
    # SECRET_KEY is a result of executing the following command in bash: openssl rand -hex 32
    SECRET_KEY=key
    
    # Production server settings
    DB_USER=postgres
    DB_PASSWORD=1234
    DB_NAME=postgres
    DB_HOST=db
    DB_PORT=5432
    
    # Test server settings
    DB_USER_TEST=postgres
    DB_PASS_TEST=1234
    DB_NAME_TEST=postgres
    DB_HOST_TEST=test-db
    DB_PORT_TEST=5432

```

## Installation

_Below is an example of how you can instruct your audience on installing and setting up your app. This template doesn't rely on any external dependencies or services._

1. Clone the repo
   ```bash
   git clone https://github.com/Arahit0gami/test_webtronics.git
   ```
2. Specify the necessary settings that are mentioned in [Prerequisites](#prerequisites).
3. In root directory run script.sh
   ```
   ./script.sh
   ```


## Documentation

All API descriptions can be found at the following addresses:

- <http://127.0.0.1:8000/docs>

- <http://127.0.0.1:8000/redoc>


## Author
[Kuzmenko Nikita](https://github.com/arahitogami)


## P.S.
Just a note for those who will be watching this test assignment. 
No feedback has been received from the company, so I don't know how well or poorly the assignment was done.


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[fastapi.tiangolo.com]: https://img.shields.io/badge/FastAPI-0.101.0-green?style=plastic&logo=FastAPI
[Fastapi-url]: https://fastapi.tiangolo.com
[Python.org]: https://img.shields.io/badge/Python-3.11.0-green?style=plastic&logo=python
[Python-url]: https://python.org
[sqlalchemy.org]: https://img.shields.io/badge/SQLAlchemy-2.0.19-green?style=plastic&logo=SqlAlchemy
[sqlalchemy-url]: https://sqlalchemy.org 
[postgresql.org]: https://img.shields.io/badge/PostgreSQL-15.0-green?style=plastic&logo=postgresql
[Postgresql-url]: https://postgresql.org
[docs.pytest.org]: https://img.shields.io/badge/Pytest-7.4.0-green?style=plastic&logo=pytest
[Pytest-url]: https://docs.pytest.org
[docker.com]: https://img.shields.io/badge/Docker--compose-3.8-green?style=plastic&logo=docker
[Docker-url]: https://docker.com
[nginx.org]: https://img.shields.io/badge/Nginx-3.8-green?style=plastic&logo=nginx
[Nginx-url]: https://nginx.org
[docs.pydantic.dev]: https://img.shields.io/badge/Pydantic-2.1.1-green?style=plastic&logo=pydantic
[Pydantic-url]: https://docs.pydantic.dev
