"""Preview and optionally normalize stored postal addresses."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections, router, transaction
from django.utils.translation import gettext as _
from geoaddress import normalize_address

from django_geoaddress.fields import GeoaddressField

if TYPE_CHECKING:
    from argparse import ArgumentParser
    from collections.abc import Iterator

    from django.db.models import Model, QuerySet


def _address_fields(database: str) -> Iterator[GeoaddressField]:
    connection = connections[database]
    models = sorted(
        apps.get_models(),
        key=lambda model: model._meta.label,  # ruff: ignore[private-member-access]
    )
    for model in models:
        meta = model._meta  # ruff: ignore[private-member-access]
        if not meta.can_migrate(connection):
            continue
        if not router.allow_migrate_model(database, model):
            continue
        for field in meta.local_concrete_fields:
            if isinstance(field, GeoaddressField):
                yield field


def _changes(
    rows: QuerySet[Model],
    field: str,
) -> Iterator[tuple[object, dict[str, object]]]:
    for pk, address in rows.values_list('pk', field).iterator():
        if not isinstance(address, dict):
            continue
        cleaned = normalize_address(address)
        if cleaned != address:
            yield pk, cleaned


def _apply_changes(rows: QuerySet[Model], field: str) -> int:
    with transaction.atomic(using=rows.db):
        # Re-read after confirmation so that the preview cannot overwrite edits.
        return sum(
            rows.filter(pk=pk).update(**{field: cleaned})
            for pk, cleaned in _changes(rows.select_for_update(), field)
        )


class Command(BaseCommand):
    """Normalize Django address fields with per-field confirmation."""

    help = _('Preview normalization of stored GeoaddressField values.')

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register write mode and database selection.

        Args:
            parser: Parser for this management command.
        """
        parser.add_argument(
            '--apply',
            action='store_true',
            help=_('Write changes after confirming each field.'),
        )
        parser.add_argument(
            '--database',
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help=_('Database to scan (default: default).'),
        )

    def handle(self, *_args: str, **options) -> None:
        """Preview each field and optionally apply confirmed changes."""
        for field in _address_fields(options['database']):
            self._process_field(
                field,
                options['database'],
                apply=options['apply'],
            )

    def _process_field(
        self,
        field: GeoaddressField,
        database: str,
        *,
        apply: bool,
    ) -> None:
        model = field.model
        meta = model._meta  # ruff: ignore[private-member-access]
        label = f'{meta.label}.{field.name}'
        manager = model._base_manager  # ruff: ignore[private-member-access]
        rows = manager.using(database).order_by('pk')
        count = sum(1 for _ in _changes(rows, field.name))
        self.stdout.write(
            _('%(field)s: %(count)d to normalize')
            % {'field': label, 'count': count},
        )
        if not (apply and count and self._confirm(label)):
            return
        updated = _apply_changes(rows, field.name)
        self.stdout.write(
            _('%(field)s: %(count)d normalized')
            % {'field': label, 'count': updated},
        )

    def _confirm(self, label: str) -> bool:
        self.stdout.write(
            _('Normalize %(field)s? [y/N] ') % {'field': label},
            ending='',
        )
        self.stdout.flush()
        answer = sys.stdin.readline()
        if not answer:
            message = _('No confirmation received; stopping.')
            raise CommandError(message)
        return answer.strip().casefold() in {'y', 'yes'}
