from sqlalchemy import event
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria

from app.db.models.mixins import SoftDeleteMixin

_soft_delete_filter_registered: bool = False


def register_soft_delete_filter() -> None:
    """Register the global soft-delete ORM filter."""
    global _soft_delete_filter_registered  # noqa: PLW0603
    if _soft_delete_filter_registered:
        return

    @event.listens_for(Session, "do_orm_execute")
    def _apply_soft_delete_filter(state: ORMExecuteState) -> None:
        """Exclude soft-deleted rows unless include_deleted is set."""
        if state.execution_options.get("include_deleted"):
            return
        if not state.is_select or state.is_column_load:
            return
        state.statement = state.statement.options(
            with_loader_criteria(
                SoftDeleteMixin,
                lambda cls: cls.deleted_at.is_(None),
                include_aliases=True,
            ),
        )

    _soft_delete_filter_registered = True
