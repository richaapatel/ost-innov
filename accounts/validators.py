from django.core.exceptions import ValidationError


class PasswordComplexityValidator:
    """Enforce the password policy used by account registration."""

    def validate(self, password, user=None):
        errors = []
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        if len(password) > 128:
            errors.append('Password must be no more than 128 characters long.')
        if not any(character.isupper() for character in password):
            errors.append('Password must contain at least one uppercase letter.')
        if not any(character.islower() for character in password):
            errors.append('Password must contain at least one lowercase letter.')
        if not any(character.isdigit() for character in password):
            errors.append('Password must contain at least one number.')
        if not any(not character.isalnum() for character in password):
            errors.append('Password must contain at least one special character.')

        if errors:
            raise ValidationError(errors, code='password_too_weak')

    def get_help_text(self):
        return (
            'Your password must be 8–128 characters and include uppercase, lowercase, '
            'a number, and a special character.'
        )
