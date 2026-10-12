from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible


@deconstructible
class MaxFileSizeValidator:
    """Reject files larger than ``settings.MAX_UPLOAD_SIZE_MB`` megabytes."""

    def __call__(self, file):
        limit_mb = settings.MAX_UPLOAD_SIZE_MB
        if file.size > limit_mb * 1024 * 1024:
            raise ValidationError(
                "The file is too large (maximum %(limit)s MB).",
                code="file_too_large",
                params={"limit": limit_mb},
            )

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator)


validate_image_extension = FileExtensionValidator(
    allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS
)
validate_file_size = MaxFileSizeValidator()
