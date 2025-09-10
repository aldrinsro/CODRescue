from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from etiquettes_pro.models import EtiquetteTemplate, Etiquette


class Command(BaseCommand):
    help = 'Configure les permissions pour les opérateurs de supervision d\'étiquettes'

    def handle(self, *args, **options):
        self.stdout.write('Configuration des permissions pour les opérateurs de supervision...')
        
        # Utiliser le groupe existant des superviseurs (opérateurs de supervision)
        superviseurs_group, created = Group.objects.get_or_create(name='superviseur')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Groupe "superviseur" créé avec succès')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Groupe "superviseur" existe déjà')
            )
        
        # Récupérer les permissions des modèles d'étiquettes
        template_permissions = Permission.objects.filter(
            content_type__app_label='etiquettes_pro',
            content_type__model__in=['etiquettetemplate', 'etiquette']
        )
        
        # Ajouter toutes les permissions au groupe des superviseurs
        for permission in template_permissions:
            superviseurs_group.permissions.add(permission)
        
        self.stdout.write(
            self.style.SUCCESS(f'{template_permissions.count()} permissions ajoutées au groupe "superviseur"')
        )
        
        # Afficher les permissions configurées
        self.stdout.write('\nPermissions configurées :')
        for permission in template_permissions:
            self.stdout.write(f'  - {permission.name} ({permission.codename})')
        
        self.stdout.write(
            self.style.SUCCESS('\nConfiguration terminée avec succès !')
        )
        
        self.stdout.write('\nPour ajouter un utilisateur au groupe des opérateurs de supervision :')
        self.stdout.write('1. Aller dans l\'admin Django')
        self.stdout.write('2. Utilisateurs > Sélectionner l\'utilisateur')
        self.stdout.write('3. Groupes > Ajouter "superviseur"')
        self.stdout.write('4. Sauvegarder')
        self.stdout.write('\nOU utiliser le script generate_operators.py pour créer des opérateurs de supervision.')
