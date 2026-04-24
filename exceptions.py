class NotFoundError(Exception):
    def __init__(self, entity: str, entity_id: int) -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} with id={entity_id} not found")


class BusinessRuleError(Exception):
    """Raised when a request violates a domain rule (not a 404)."""


class AuthenticationError(Exception):
    """Raised when credentials are missing, invalid, or expired."""


class AuthorizationError(Exception):
    """Raised when a valid user lacks permission for the requested action."""
