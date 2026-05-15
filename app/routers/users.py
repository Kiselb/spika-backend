from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from .. import models, schemas, security
from ..constants import RoleEnum
from .utils import update_user_fields
from ..security import user_has_role, user_has_any_role

router = APIRouter(prefix="/Users", tags=["Users"])

def get_user_or_404(
    user_id: int,
    db: Session
) -> models.User:
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def check_admin_can_modify(
    target: models.User
):
    """Админ не может изменять пользователей с ролью SUBJECT"""
    if user_has_role(target, RoleEnum.SUBJECT):
        raise HTTPException(status_code=403, detail="Cannot modify users with SUBJECT role")

def load_user_with_relations(
    user_id: int,
    db: Session,
    include_survey: bool = False
) -> models.User:
    """Загружает пользователя с education и roles, опционально с survey"""
    options = [
        joinedload(models.User.education),
        joinedload(models.User.roles)
    ]
    if include_survey:
        options.append(joinedload(models.User.survey).joinedload(models.Survey.types_of_thinking))
    return db.query(models.User).options(*options).filter(models.User.user_id == user_id).first()

@router.post("", response_model=schemas.UserOut, status_code=201)
def create_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_role(RoleEnum.ADMIN))
):
    # Проверки уникальности
    if db.query(models.User).filter(models.User.telegram_id == user_data.telegram_id).first():
        raise HTTPException(status_code=400, detail="User with this telegram_id already exists")
    if user_data.telegram and db.query(models.User).filter(models.User.telegram == user_data.telegram).first():
        raise HTTPException(status_code=400, detail="Telegram username already in use")
    if user_data.email and db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Создание пользователя
    user = models.User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        middle_name=user_data.middle_name,
        position=user_data.position,
        education_id=user_data.education_id,
        email=user_data.email,
        telegram=user_data.telegram,
        date_of_birth=user_data.date_of_birth,
        gender=user_data.gender.value if user_data.gender else None,
        married=user_data.married,
        children=user_data.children,
        telegram_id=user_data.telegram_id,
    )
    db.add(user)
    db.flush()  # чтобы получить user.user_id

    # Назначение ролей (если переданы)
    if user_data.roles:
        role_objects = db.query(models.Role).filter(models.Role.role_name.in_([r.value for r in user_data.roles])).all()
        for role in role_objects:
            db.add(models.UserRole(user_id=user.user_id, role_id=role.role_id))

    db.commit()

    # Загружаем пользователя с ролями и образованием, но без опроса
    user = load_user_with_relations(user.user_id, db, include_survey=False)
    return user

@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    target = get_user_or_404(user_id, db)

    # SUBJECT не может смотреть чужие профили
    if user_has_role(current_user, RoleEnum.SUBJECT):
        if current_user.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        # Если смотрит свой профиль, это делается через /Profile -- неверный запрос
        raise HTTPException(status_code=400, detail="Access denied")

    # EXPERT и DEVELOPER могут смотреть только SUBJECT, причём с опросом
    if user_has_any_role(current_user, RoleEnum.EXPERT, RoleEnum.DEVELOPER):
        if not user_has_role(target, RoleEnum.SUBJECT):
            raise HTTPException(status_code=403, detail="You can only view SUBJECT users")
        return load_user_with_relations(user_id, db, include_survey=True)

    # ADMIN может смотреть любого, но без опроса
    if user_has_role(current_user, RoleEnum.ADMIN):
        return load_user_with_relations(user_id, db, include_survey=False)

    raise HTTPException(status_code=403, detail="Forbidden")

@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    user_data: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_role(RoleEnum.ADMIN))
):
    target = get_user_or_404(user_id, db)
    check_admin_can_modify(target, current_user)

    # Проверки уникальности
    if user_data.telegram and user_data.telegram != target.telegram:
        if db.query(models.User).filter(models.User.telegram == user_data.telegram).first():
            raise HTTPException(status_code=400, detail="Telegram username already in use")
    if user_data.email and user_data.email != target.email:
        if db.query(models.User).filter(models.User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")

    update_user_fields(target, user_data)
    db.commit()

    # Возвращаем без опроса
    return load_user_with_relations(user_id, db, include_survey=False)


@router.put("/{user_id}/roles", response_model=schemas.UserOut)
def update_user_roles(
    user_id: int,
    roles_data: schemas.UserRolesUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_role(RoleEnum.ADMIN))
):
    target = get_user_or_404(user_id, db)
    check_admin_can_modify(target, current_user)

    # Получаем объекты ролей (без SUBJECT – уже проверено в схеме)
    role_names = [r.value for r in roles_data.roles]
    new_roles = db.query(models.Role).filter(models.Role.role_name.in_(role_names)).all()

    # Удаляем старые связи
    db.query(models.UserRole).filter(models.UserRole.user_id == user_id).delete()
    # Добавляем новые
    for role in new_roles:
        db.add(models.UserRole(user_id=user_id, role_id=role.role_id))

    db.commit()

    # Возвращаем пользователя с обновлёнными ролями, без опроса
    return load_user_with_relations(user_id, db, include_survey=False)
