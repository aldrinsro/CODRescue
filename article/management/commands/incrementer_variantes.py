import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from article.models import Article, VarianteArticle, Couleur, Pointure, Categorie, Genre
from decimal import Decimal


class Command(BaseCommand):
    help = 'Incrémente toutes les variantes d\'articles avec une quantité de 50'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='articles_clean.csv',
            help='Chemin vers le fichier CSV des articles (défaut: articles_clean.csv)'
        )
        parser.add_argument(
            '--quantite',
            type=int,
            default=50,
            help='Quantité à ajouter à chaque variante (défaut: 50)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la création des variantes même si elles existent déjà'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        quantite = options['quantite']
        dry_run = options['dry_run']
        force = options['force']

        # Vérifier que le fichier CSV existe
        if not os.path.exists(csv_file):
            raise CommandError(f'Le fichier CSV "{csv_file}" n\'existe pas.')

        self.stdout.write(
            self.style.SUCCESS(f'Début de l\'incrémentation des variantes avec une quantité de {quantite}')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODE DRY-RUN: Aucune modification ne sera effectuée')
            )

        # Statistiques
        stats = {
            'articles_traites': 0,
            'variantes_creees': 0,
            'variantes_incrementees': 0,
            'erreurs': 0,
            'couleurs_creees': 0,
            'pointures_creees': 0
        }

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # Commence à 2 car la ligne 1 est l'en-tête
                    try:
                        self.process_article_row(row, quantite, dry_run, force, stats)
                        stats['articles_traites'] += 1
                        
                        if row_num % 10 == 0:  # Afficher le progrès tous les 10 articles
                            self.stdout.write(f'Articles traités: {stats["articles_traites"]}')
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Erreur ligne {row_num}: {str(e)}')
                        )
                        stats['erreurs'] += 1
                        continue

        except Exception as e:
            raise CommandError(f'Erreur lors de la lecture du fichier CSV: {str(e)}')

        # Afficher les statistiques finales
        self.display_final_stats(stats, dry_run)

    def process_article_row(self, row, quantite, dry_run, force, stats):
        """Traite une ligne du CSV pour un article"""
        ref_article = row.get('REF ARTICLE', '').strip()
        if not ref_article:
            return

        # Extraire les informations de l'article
        nom_article = ref_article
        categorie_nom = row.get('CATEGORIE', '').strip()
        genre_nom = row.get('GENRE', '').strip()
        prix_unitaire = self.parse_decimal(row.get('PRIX UNITAIRE', '0'))
        pointures_str = row.get('POINTURE', '').strip()
        couleurs_str = row.get('COULEUR', '').strip()
        phase = self.map_phase(row.get('PHASE', 'EN COURS').strip())

        # Créer ou récupérer l'article
        article = self.get_or_create_article(
            ref_article, nom_article, categorie_nom, genre_nom, 
            prix_unitaire, phase, dry_run, stats
        )

        if not article:
            return

        # Traiter les couleurs et pointures
        couleurs = self.parse_couleurs(couleurs_str)
        pointures = self.parse_pointures(pointures_str)

        # Créer les variantes
        self.create_variantes(
            article, couleurs, pointures, quantite, dry_run, force, stats
        )

    def get_or_create_article(self, ref_article, nom_article, categorie_nom, 
                            genre_nom, prix_unitaire, phase, dry_run, stats):
        """Crée ou récupère un article"""
        try:
            # Chercher l'article par référence
            article = Article.objects.filter(reference=ref_article).first()
            
            if article:
                if not dry_run:
                    # Mettre à jour les informations si nécessaire
                    if article.prix_unitaire != prix_unitaire:
                        article.prix_unitaire = prix_unitaire
                        article.save()
                return article

            # Créer la catégorie si elle n'existe pas
            categorie = self.get_or_create_categorie(categorie_nom, dry_run, stats)
            if not categorie:
                return None

            # Créer le genre si il n'existe pas
            genre = self.get_or_create_genre(genre_nom, dry_run, stats)
            if not genre:
                return None

            if dry_run:
                self.stdout.write(f'  ARTICLE: {nom_article} - {categorie_nom} - {genre_nom}')
                return None

            # Créer l'article
            article = Article.objects.create(
                nom=nom_article,
                reference=ref_article,
                prix_unitaire=prix_unitaire,
                categorie=categorie,
                genre=genre,
                phase=phase,
                actif=True
            )

            self.stdout.write(f'  ARTICLE CRÉÉ: {nom_article}')
            return article

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la création de l\'article {nom_article}: {str(e)}')
            )
            return None

    def get_or_create_categorie(self, categorie_nom, dry_run, stats):
        """Crée ou récupère une catégorie"""
        if not categorie_nom:
            return None

        # Mapping des catégories
        categorie_mapping = {
            'CHAUSSURE': 'CHAUSSURES',
            'SANDALE': 'SANDALES',
            'ESPADRILLE': 'ESPARILLE',
            'MULES': 'MULES',
            'SABOT': 'SABOT',
            'ESCARPINS': 'ESCARPINS',
            'BOTTE': 'BOTTE',
            'PACK': 'PACK_SAC',
            'FOULARD': 'PACK_SAC',  # Mapping vers PACK_SAC
            'CHALE': 'PACK_SAC',    # Mapping vers PACK_SAC
            'SAC': 'PACK_SAC',      # Mapping vers PACK_SAC
        }

        categorie_clean = categorie_mapping.get(categorie_nom.upper(), categorie_nom.upper())

        try:
            categorie, created = Categorie.objects.get_or_create(
                nom=categorie_clean,
                defaults={'actif': True}
            )
            
            if created and not dry_run:
                stats['couleurs_creees'] += 1  # Réutiliser le compteur pour les catégories
                self.stdout.write(f'  CATÉGORIE CRÉÉE: {categorie_clean}')
            
            return categorie

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la création de la catégorie {categorie_clean}: {str(e)}')
            )
            return None

    def get_or_create_genre(self, genre_nom, dry_run, stats):
        """Crée ou récupère un genre"""
        if not genre_nom:
            return None

        # Mapping des genres
        genre_mapping = {
            'FEMME': 'FEMME',
            'HOMME': 'HOMME',
            'FILLE': 'FILLE',
            'GARCON': 'GARCON',
            'GARCON, FILLE': 'FILLE',  # Prendre le premier genre
        }

        genre_clean = genre_mapping.get(genre_nom.upper(), genre_nom.upper())

        try:
            genre, created = Genre.objects.get_or_create(
                nom=genre_clean,
                defaults={'actif': True}
            )
            
            if created and not dry_run:
                stats['pointures_creees'] += 1  # Réutiliser le compteur pour les genres
                self.stdout.write(f'  GENRE CRÉÉ: {genre_clean}')
            
            return genre

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la création du genre {genre_clean}: {str(e)}')
            )
            return None

    def create_variantes(self, article, couleurs, pointures, quantite, dry_run, force, stats):
        """Crée les variantes pour un article"""
        if not couleurs or not pointures:
            return

        for couleur_nom in couleurs:
            for pointure_nom in pointures:
                try:
                    # Créer ou récupérer la couleur
                    couleur = self.get_or_create_couleur(couleur_nom, dry_run, stats)
                    if not couleur:
                        continue

                    # Créer ou récupérer la pointure
                    pointure = self.get_or_create_pointure(pointure_nom, dry_run, stats)
                    if not pointure:
                        continue

                    # Vérifier si la variante existe déjà
                    variante_existante = VarianteArticle.objects.filter(
                        article=article,
                        couleur=couleur,
                        pointure=pointure
                    ).first()

                    if variante_existante:
                        if force:
                            if not dry_run:
                                variante_existante.qte_disponible += quantite
                                variante_existante.save()
                            stats['variantes_incrementees'] += 1
                            self.stdout.write(
                                f'    VARIANTE INCRÉMENTÉE: {couleur_nom} - {pointure_nom} (+{quantite})'
                            )
                        else:
                            self.stdout.write(
                                f'    VARIANTE EXISTANTE IGNORÉE: {couleur_nom} - {pointure_nom}'
                            )
                    else:
                        if not dry_run:
                            variante = VarianteArticle.objects.create(
                                article=article,
                                couleur=couleur,
                                pointure=pointure,
                                qte_disponible=quantite,
                                actif=True
                            )
                            # Générer la référence automatiquement
                            variante.reference_variante = variante.generer_reference_variante_automatique()
                            variante.save()
                        
                        stats['variantes_creees'] += 1
                        self.stdout.write(
                            f'    VARIANTE CRÉÉE: {couleur_nom} - {pointure_nom} (qte: {quantite})'
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'    Erreur variante {couleur_nom}-{pointure_nom}: {str(e)}')
                    )

    def get_or_create_couleur(self, couleur_nom, dry_run, stats):
        """Crée ou récupère une couleur"""
        if not couleur_nom:
            return None

        try:
            couleur, created = Couleur.objects.get_or_create(
                nom=couleur_nom,
                defaults={'actif': True}
            )
            
            if created and not dry_run:
                stats['couleurs_creees'] += 1
                self.stdout.write(f'  COULEUR CRÉÉE: {couleur_nom}')
            
            return couleur

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la création de la couleur {couleur_nom}: {str(e)}')
            )
            return None

    def get_or_create_pointure(self, pointure_nom, dry_run, stats):
        """Crée ou récupère une pointure"""
        if not pointure_nom:
            return None

        try:
            # Essayer de convertir en entier pour l'ordre
            ordre = 0
            if pointure_nom.isdigit():
                ordre = int(pointure_nom)

            pointure, created = Pointure.objects.get_or_create(
                pointure=pointure_nom,
                defaults={'actif': True, 'ordre': ordre}
            )
            
            if created and not dry_run:
                stats['pointures_creees'] += 1
                self.stdout.write(f'  POINTURE CRÉÉE: {pointure_nom}')
            
            return pointure

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la création de la pointure {pointure_nom}: {str(e)}')
            )
            return None

    def parse_couleurs(self, couleurs_str):
        """Parse la chaîne de couleurs"""
        if not couleurs_str:
            return []
        
        # Nettoyer et séparer les couleurs
        couleurs = []
        for couleur in couleurs_str.split('-'):
            couleur_clean = couleur.strip()
            if couleur_clean and couleur_clean not in couleurs:
                couleurs.append(couleur_clean)
        
        return couleurs

    def parse_pointures(self, pointures_str):
        """Parse la chaîne de pointures"""
        if not pointures_str:
            return []
        
        pointures = []
        
        # Gérer les plages de pointures (ex: 37---41, 40 - 44)
        if '---' in pointures_str or ' - ' in pointures_str:
            # Extraire les plages
            parts = pointures_str.replace('---', '-').replace(' - ', '-').split('-')
            if len(parts) >= 2:
                try:
                    debut = int(parts[0].strip())
                    fin = int(parts[-1].strip())
                    for i in range(debut, fin + 1):
                        pointures.append(str(i))
                except ValueError:
                    # Si ce n'est pas une plage numérique, traiter comme des pointures individuelles
                    pointures = [p.strip() for p in pointures_str.split(',') if p.strip()]
        else:
            # Pointures individuelles
            pointures = [p.strip() for p in pointures_str.split(',') if p.strip()]
        
        return pointures

    def parse_decimal(self, value):
        """Parse une valeur décimale"""
        try:
            return Decimal(str(value).replace(',', '.'))
        except:
            return Decimal('0.00')

    def map_phase(self, phase_str):
        """Mappe la phase du CSV vers les choix du modèle"""
        phase_mapping = {
            'EN COURS': 'EN_COURS',
            'LIQUIDATION': 'LIQUIDATION',
            'EN TEST': 'EN_TEST',
            'PROMO': 'PROMO',
        }
        return phase_mapping.get(phase_str.upper(), 'EN_COURS')

    def display_final_stats(self, stats, dry_run):
        """Affiche les statistiques finales"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('RÉSUMÉ DE L\'OPÉRATION'))
        self.stdout.write('='*50)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODE DRY-RUN - Aucune modification effectuée'))
        
        self.stdout.write(f'Articles traités: {stats["articles_traites"]}')
        self.stdout.write(f'Variantes créées: {stats["variantes_creees"]}')
        self.stdout.write(f'Variantes incrémentées: {stats["variantes_incrementees"]}')
        self.stdout.write(f'Couleurs créées: {stats["couleurs_creees"]}')
        self.stdout.write(f'Pointures créées: {stats["pointures_creees"]}')
        self.stdout.write(f'Erreurs: {stats["erreurs"]}')
        
        if stats['erreurs'] > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠️  {stats["erreurs"]} erreurs ont été rencontrées. Vérifiez les logs ci-dessus.')
            )
        
        if not dry_run and (stats['variantes_creees'] > 0 or stats['variantes_incrementees'] > 0):
            self.stdout.write(
                self.style.SUCCESS('✅ Opération terminée avec succès!')
            )
