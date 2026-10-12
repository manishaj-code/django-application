from django.db import models


class ContactMessage(models.Model):
    """A message submitted through the public contact form."""

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField(max_length=5000)
    is_read = models.BooleanField("read", default=False)
    created_at = models.DateTimeField("received", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "contact message"

    def __str__(self):
        return f"{self.subject} — {self.name}"
