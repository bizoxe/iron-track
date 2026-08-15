from advanced_alchemy.service import OffsetPagination

from app.domain.accounts.schemas import User, UserAuth
from app.domain.catalogs.schemas import EquipmentRead, MuscleGroupRead, TagRead
from app.domain.exercises.schemas import ExerciseRead

MSGSPEC_SCHEMAS = (
    User,
    UserAuth,
    OffsetPagination[User],
    ExerciseRead,
    OffsetPagination[ExerciseRead],
    MuscleGroupRead,
    EquipmentRead,
    TagRead,
)
