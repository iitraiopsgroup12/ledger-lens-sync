"""Domain exceptions raised by the service layer."""


class NotFoundError(Exception):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity: str, entity_id: str) -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} with id '{entity_id}' was not found")


class ConflictError(Exception):
    """Raised when a write would violate a uniqueness/business rule."""

    def __init__(self, message: str) -> None:
        super().__init__(message)