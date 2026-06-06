"""
Django management command: python manage.py seed_db

Place this file at:
  backend/apps/users/management/commands/seed_db.py

Create the folder structure first:
  mkdir -p backend/apps/users/management/commands
  touch backend/apps/users/management/__init__.py
  touch backend/apps/users/management/commands/__init__.py
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Seed the database with 200 Sri Lankan microfinance clients and realistic loan data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt and run immediately',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  This will DELETE all existing non-superuser data and reseed.\n'
                    '   Run with --confirm to proceed: python manage.py seed_db --confirm\n'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('Starting database seed...'))

        # Import and run the seed function
        import sys
        import os
        # Add the backend directory to path so seed_data.py can be found
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )))
        sys.path.insert(0, backend_dir)

        # Import seed function directly
        from seed_data import seed_database
        seed_database()
