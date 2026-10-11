"""Simple User data structure for LOCUS."""


class User:
    """Represents a row in the ``users`` table.

    No database queries live here – this is a plain data container.
    """

    def __init__(
        self,
        user_id,
        name,
        email,
        student_id,
        password=None,
        created_at=None,
    ):
        self.user_id    = user_id
        self.name       = name
        self.email      = email
        self.student_id = student_id
        self.password   = password      # bcrypt hash; omit when not needed
        self.created_at = created_at

    def to_dict(self, include_password=False):
        """Return the user as a plain dictionary.

        The password hash is excluded by default.
        """
        data = {
            "user_id":    self.user_id,
            "name":       self.name,
            "email":      self.email,
            "student_id": self.student_id,
            "created_at": str(self.created_at) if self.created_at else None,
        }
        if include_password:
            data["password"] = self.password
        return data

    def __repr__(self):
        return (
            f"User(user_id={self.user_id!r}, name={self.name!r}, "
            f"email={self.email!r}, student_id={self.student_id!r})"
        )
