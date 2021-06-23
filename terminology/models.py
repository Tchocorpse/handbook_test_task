from django.db import models
from django.db.models import (
    AutoField,
    CharField,
    TextField,
    ForeignKey,
    ManyToManyField,
)
from django.utils import timezone


class Handbook(models.Model):
    id = AutoField(primary_key=True)

    name = CharField(
        verbose_name="Наименование", max_length=255, blank=False, null=False
    )
    short_name = CharField(
        verbose_name="Короткое наименование", max_length=10, blank=False, null=False
    )
    description = TextField(verbose_name="Описание", blank=False, null=False)

    def __str__(self):
        return self.name


class HandbookVersion(models.Model):
    id = AutoField(primary_key=True)
    handbook_identifier = ForeignKey(
        Handbook,
        related_name="versions",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )

    version = CharField(verbose_name="Версия", max_length=255, blank=False, null=False)
    starting_date = models.DateTimeField(
        auto_now_add=False, default=timezone.now, blank=False, null=False
    )

    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now=True, blank=False, null=False)

    def __str__(self):
        return f"{self.handbook_identifier} версия {self.version}"

    def save(self, *args, **kwargs):
        if not self.starting_date:
            self.starting_date = self.created
        super(HandbookVersion, self).save(*args, **kwargs)


class HandbookElement(models.Model):
    id = AutoField(primary_key=True)
    handbook = ManyToManyField(HandbookVersion, blank=False, null=False)

    element_code = CharField(
        verbose_name="Код элемента", max_length=255, blank=False, null=False
    )
    element_value = CharField(
        verbose_name="Значение элемента", max_length=255, blank=False, null=False
    )

    def list_handbooks(self):
        return "\n, ".join([str(h) for h in self.handbook.all()])
