from ..schemas.user import ProfileUpdate

def update_user_fields(user, data: ProfileUpdate):
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.middle_name is not None:
        user.middle_name = data.middle_name
    if data.position is not None:
        user.position = data.position
    if data.education_id is not None:
        user.education_id = data.education_id
    if data.email is not None:
        user.email = data.email
    if data.telegram is not None:
        user.telegram = data.telegram
    if data.date_of_birth is not None:
        user.date_of_birth = data.date_of_birth
    if data.gender is not None:
        user.gender = data.gender.value
    if data.married is not None:
        user.married = data.married
    if data.children is not None:
        user.children = data.children
