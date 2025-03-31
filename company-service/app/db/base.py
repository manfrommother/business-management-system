# Импорт базового класса для декларативных моделей
from app.db.base_class import Base

# Импорт всех моделей SQLAlchemy здесь
# Это необходимо для Alembic, чтобы он мог обнаружить модели
# при генерации миграций.
from app.models.company import Company  # noqa
from app.models.department import Department  # noqa
from app.models.membership import Membership  # noqa
from app.models.invitation import Invitation  # noqa
from app.models.news import News  # noqa

# Пример:
# from app.models.company import Company
# from app.models.department import Department
# from app.models.membership import Membership
# from app.models.invitation import Invitation
# from app.models.news import News 