from django.core.management.base import BaseCommand
import os
import platform

class Command(BaseCommand):
    help = 'Configure la tâche périodique pour traiter les confirmations décalées'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Configuration de la tâche périodique pour les confirmations décalées...')
        )
        
        # Chemin vers le projet
        project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        manage_py_path = os.path.join(project_path, 'manage.py')
        
        # Commande à exécuter
        command = f'python {manage_py_path} process_delayed_confirmations'
        
        if platform.system() == 'Windows':
            self.stdout.write(
                self.style.WARNING('Pour Windows, configurez une tâche planifiée :')
            )
            self.stdout.write('')
            self.stdout.write('1. Ouvrez le Planificateur de tâches Windows')
            self.stdout.write('2. Créez une tâche de base')
            self.stdout.write('3. Configurez :')
            self.stdout.write(f'   - Nom: "YZ-CMD - Confirmations décalées"')
            self.stdout.write(f'   - Déclencheur: Toutes les 5 minutes')
            self.stdout.write(f'   - Action: Démarrer un programme')
            self.stdout.write(f'   - Programme: python')
            self.stdout.write(f'   - Arguments: {manage_py_path} process_delayed_confirmations')
            self.stdout.write(f'   - Dossier de départ: {project_path}')
            self.stdout.write('')
            self.stdout.write('Ou utilisez PowerShell pour créer la tâche :')
            self.stdout.write('')
            self.stdout.write(f'$action = New-ScheduledTaskAction -Execute "python" -Argument "{manage_py_path} process_delayed_confirmations" -WorkingDirectory "{project_path}"')
            self.stdout.write('$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)')
            self.stdout.write('$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable')
            self.stdout.write('Register-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -TaskName "YZ-CMD-Confirmations-Delayed" -Description "Traite les confirmations décalées automatiquement"')
            
        else:
            # Linux/Mac - Crontab
            self.stdout.write(
                self.style.WARNING('Pour Linux/Mac, ajoutez cette ligne au crontab :')
            )
            self.stdout.write('')
            self.stdout.write('# Traiter les confirmations décalées toutes les 5 minutes')
            self.stdout.write('*/5 * * * * cd ' + project_path + ' && ' + command)
            self.stdout.write('')
            self.stdout.write('Pour l\'ajouter au crontab, exécutez :')
            self.stdout.write('crontab -e')
            self.stdout.write('')
            self.stdout.write('Ou utilisez cette commande :')
            self.stdout.write(f'echo "*/5 * * * * cd {project_path} && {command}" | crontab -')
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('Configuration terminée !')
        )
        self.stdout.write('')
        self.stdout.write('INFO: La commande sera exécutée toutes les 5 minutes pour traiter les confirmations décalées.')
        self.stdout.write('INFO: Vous pouvez tester manuellement avec : python manage.py process_delayed_confirmations')
