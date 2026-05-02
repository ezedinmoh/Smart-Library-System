from django.core.management.base import BaseCommand
from allauth.account.models import EmailConfirmation


class Command(BaseCommand):
    help = 'Get the most recent email verification URL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Show all pending verification URLs',
        )

    def handle(self, *args, **options):
        if options['all']:
            # Show all pending confirmations
            confirmations = EmailConfirmation.objects.order_by('-created')
            
            if not confirmations:
                self.stdout.write(self.style.WARNING('No pending email confirmations found.'))
                return
            
            self.stdout.write('\n' + '='*100)
            self.stdout.write(f'ALL PENDING VERIFICATIONS ({confirmations.count()})')
            self.stdout.write('='*100 + '\n')
            
            for conf in confirmations:
                url = f'http://127.0.0.1:8000/users/verify-email/{conf.key}/'
                self.stdout.write(f'User: {conf.email_address.user.username}')
                self.stdout.write(f'Email: {conf.email_address.email}')
                self.stdout.write(f'Created: {conf.created}')
                self.stdout.write(f'\nURL: {url}\n')
                self.stdout.write('-'*100 + '\n')
        else:
            # Show only the most recent
            confirmation = EmailConfirmation.objects.order_by('-created').first()
            
            if not confirmation:
                self.stdout.write(self.style.WARNING('No pending email confirmations found.'))
                return
            
            url = f'http://127.0.0.1:8000/users/verify-email/{confirmation.key}/'
            
            self.stdout.write('\n' + '='*100)
            self.stdout.write(self.style.SUCCESS('MOST RECENT VERIFICATION URL'))
            self.stdout.write('='*100 + '\n')
            self.stdout.write(f'User: {confirmation.email_address.user.username}')
            self.stdout.write(f'Email: {confirmation.email_address.email}')
            self.stdout.write(f'Created: {confirmation.created}')
            self.stdout.write('\n' + self.style.HTTP_INFO(url))
            self.stdout.write('\n' + '='*100 + '\n')
