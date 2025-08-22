from django.core.exceptions import ValidationError
import re

class HIPAAPasswordValidator:
    def validate(self, password: str, user=None) -> None:
        if len(password) < 12:
            raise ValidationError("Password must be at least 12 characters long.")
        if len(re.findall(r'[A-Z]', password)) < 2:
            raise ValidationError("Password must contain at least 2 uppercase letters.")
        if len(re.findall(r'[a-z]', password)) < 2:
            raise ValidationError("Password must contain at least 2 lowercase letters.")
        if len(re.findall(r'\d', password)) < 2:
            raise ValidationError("Password must contain at least 2 digits.")
        if len(re.findall(r'[!@#$%^&*(),.?":{}|<>]', password)) < 2:
            raise ValidationError("Password must contain at least 2 special characters.")

    def get_help_text(self) -> str:
        return (
            "Your password must be at least 12 characters long and include at least "
            "2 uppercase letters, 2 lowercase letters, 2 numbers, and 2 special characters."
        )
