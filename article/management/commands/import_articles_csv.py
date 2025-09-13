import csv
import os
import re
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from article.models import Article, Categorie, Genre, Pointure, Couleur, VarianteArticle
from parametre.models import Operateur


class Command(BaseCommand):
    help = 'Importe les articles depuis un fichier CSV avec leurs variantes selon la structure YOOZAK (version mise à jour)'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Chemin vers le fichier CSV à importer'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait importé sans effectuer l\'importation'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Met à jour les articles existants au lieu de les ignorer'
        )
        parser.add_argument(
            '--verbose-colors',
            action='store_true',
            help='Affiche la normalisation des couleurs pendant l\'importation'
        )
        parser.add_argument(
            '--verbose-pointures',
            action='store_true',
            help='Affiche la creation des intervalles de pointures pendant l\'importation'
        )
        parser.add_argument(
            '--regenerate-references',
            action='store_true',
            help='Force la régénération des références même si elles existent déjà'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        update_existing = options['update_existing']
        verbose_colors = options['verbose_colors']
        verbose_pointures = options['verbose_pointures']
        regenerate_references = options['regenerate_references']

        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'Le fichier {csv_file} n\'existe pas.')
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING('Mode DRY-RUN activé - Aucune donnée ne sera importée')
            )

        # Mapping des phases du CSV vers les phases du modèle
        phase_mapping = {
            'EN COUR': 'EN_COURS',
            'EN COURS': 'EN_COURS',
            'EN TEST': 'EN_TEST',
            'EN LIQUIDATION': 'LIQUIDATION',
            'LIQUIDATION': 'LIQUIDATION',
            'PROMO': 'PROMO'
        }

        # Mapping des catégories du CSV vers les catégories du modèle
        categorie_mapping = {
            'SANDALE': 'SANDALES',
            'SANDALES': 'SANDALES',
            'SABOT': 'SABOT',
            'CHAUSSURE': 'CHAUSSURES',
            'CHAUSSURES': 'CHAUSSURES',
            'ESPADRILLE': 'ESPARILLE',
            'ESPARILLES': 'ESPARILLE',
            'BASKET': 'BASKET',
            'BASKETS': 'BASKET',
            'MULES': 'MULES',
            'MULE': 'MULES',
            'PACK': 'PACK_SAC',
            'PACK_SAC': 'PACK_SAC',
            'BOTTE': 'BOTTE',
            'BOTTES': 'BOTTE',
            'ESCARPINS': 'ESCARPINS',
            'ESCARPIN': 'ESCARPINS',
            'SAC': 'PACK_SAC'  # Les sacs sont dans la catégorie PACK_SAC
        }

        # Mapping des genres du CSV vers les genres du modèle
        genre_mapping = {
            'FEMME': 'FEMME',
            'HOMME': 'HOMME',
            'FILLE': 'FILLE',
            'GARCON': 'GARCON'
        }

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                articles_created = 0
                articles_updated = 0
                articles_skipped = 0
                variantes_created = 0
                errors = []

                self.stdout.write('Demarrage de l\'importation des articles...')
                self.stdout.write(f'Fichier: {csv_file}')
                
                # Afficher les colonnes trouvées dans le CSV pour le débogage
                if hasattr(reader, 'fieldnames') and reader.fieldnames:
                    self.stdout.write(f'Colonnes detectees dans le CSV: {reader.fieldnames}')
                else:
                    self.stdout.write('Impossible de detecter les colonnes du CSV')

                for row_num, row in enumerate(reader, start=2):  # Commencer à 2 car la ligne 1 est l'en-tête
                    try:
                        # Vérifier que les données essentielles sont présentes
                        if not row.get('REF ARTICLE'):
                            self.stdout.write(
                                self.style.WARNING(f'Ligne {row_num}: Référence manquante, ignorée')
                            )
                            articles_skipped += 1
                            continue

                        # Nettoyer et valider les données - Protection contre None
                        reference = (row.get('REF ARTICLE') or '').strip()
                        nom = reference  # Le nom est égal à la référence pour l'instant
                        
                        if not reference:
                            articles_skipped += 1
                            continue

                        # Traiter la catégorie - Protection contre None
                        categorie_csv = (row.get('CATEGORIE') or '').strip().upper()
                        if categorie_csv in categorie_mapping:
                            categorie_nom = categorie_mapping[categorie_csv]
                        else:
                            categorie_nom = 'CHAUSSURES'  # Valeur par défaut

                        # Créer ou récupérer l'objet Catégorie
                        try:
                            categorie_obj = Categorie.objects.get(nom=categorie_nom)
                        except Categorie.DoesNotExist:
                            # Créer la catégorie si elle n'existe pas
                            categorie_obj = Categorie.objects.create(
                                nom=categorie_nom,
                                description=f'Catégorie {categorie_nom}',
                                actif=True
                            )

                        # Traiter le genre - Protection contre None
                        genre_csv = (row.get('GENRE') or '').strip().upper()
                        if genre_csv in genre_mapping:
                            genre_nom = genre_mapping[genre_csv]
                        else:
                            genre_nom = 'FEMME'  # Valeur par défaut

                        # Créer ou récupérer l'objet Genre
                        try:
                            genre_obj = Genre.objects.get(nom=genre_nom)
                        except Genre.DoesNotExist:
                            # Créer le genre s'il n'existe pas
                            genre_obj = Genre.objects.create(
                                nom=genre_nom,
                                description=f'Genre {genre_nom}',
                                actif=True
                            )

                        # Traiter la phase - Protection contre None
                        phase_csv = (row.get('PHASE') or '').strip().upper()
                        if phase_csv in phase_mapping:
                            phase = phase_mapping[phase_csv]
                        else:
                            phase = 'EN_COURS'  # Valeur par défaut

                        # PRIX - Traitement des prix selon les nouvelles spécifications
                        prix_unitaire = self._parse_price(row.get('PRIX UNITAIRE', ''))
                        if prix_unitaire is None:
                            prix_unitaire = Decimal('0.00')

                        prix_achat = self._parse_price(row.get('PRIX ACHAT', ''))
                        if prix_achat is None:
                            prix_achat = Decimal('0.00')

                        # Prix de liquidation
                        prix_liquidation = self._parse_price(row.get('PRIX LIQ 1', '')) or \
                                         self._parse_price(row.get('PRIX LIQUIDATION', ''))

                        # Prix upsell
                        prix_upsell_1 = self._parse_price(row.get('PRIX UPSEL 1', '')) or \
                                       self._parse_price(row.get('PRIX UPSELL 1', ''))
                        
                        prix_upsell_2 = self._parse_price(row.get('PRIX UPSEL 2', '')) or \
                                       self._parse_price(row.get('PRIX UPSELL 2', ''))
                        
                        prix_upsell_3 = self._parse_price(row.get('PRIX UPSEL 3', '')) or \
                                       self._parse_price(row.get('PRIX UPSELL 3', ''))
                        
                        prix_upsell_4 = self._parse_price(row.get('PRIX UPSEL 4', '')) or \
                                       self._parse_price(row.get('PRIX UPSELL 4', ''))

                       
                        # Description (optionnel) - Protection contre None
                        description = (row.get('DESCRIPTION') or '').strip() or None

                        # Image URL (optionnel) - Protection contre None
                        image_url = (row.get('IMAGE_URL') or '').strip() or None

                        # Déterminer si c'est un article upsell
                        is_upsell = any([
                            prix_upsell_1 is not None,
                            prix_upsell_2 is not None,
                            prix_upsell_3 is not None,
                            prix_upsell_4 is not None,
                           
                        ])

                        # Extraire le numéro de modèle de la référence (ex: YZ478 -> 478)
                        modele = self._extract_modele(reference)

                        # Traiter les pointures - Protection contre None
                        pointures_str = (row.get('POINTURE') or '').strip()
                        pointures = self._parse_pointures(pointures_str, verbose=verbose_pointures)

                        # Traiter les couleurs - Protection contre None
                        couleurs_str = (row.get('COULEUR') or '').strip()
                        couleurs = self._parse_couleurs(couleurs_str)
                        
                        # Afficher les couleurs normalisées pour le suivi (si option activée)
                        if verbose_colors and couleurs_str and couleurs_str != '':
                            self.stdout.write(f'Couleurs CSV: "{couleurs_str}" -> Normalisees: {couleurs}')

                        # Vérifier si l'article existe déjà
                        article_existant = None
                        if reference:
                            article_existant = Article.objects.filter(reference=reference).first()
                        else:
                            # Si pas de référence, chercher par nom
                            article_existant = Article.objects.filter(nom=nom).first()

                        if article_existant and not update_existing:
                            self.stdout.write(
                                self.style.WARNING(f'Article existant ignore: {nom} - {reference}')
                            )
                            articles_skipped += 1
                            continue

                        # Créer ou mettre à jour l'article
                        if dry_run:
                            if article_existant:
                                self.stdout.write(f'[DRY-RUN] Article a mettre a jour: {nom} - {reference}')
                            else:
                                self.stdout.write(f'[DRY-RUN] Article a creer: {nom} - {reference}')
                            
                            # Afficher les prix qui seraient importés
                            self.stdout.write(f'  Prix unitaire: {prix_unitaire} DH')
                            if prix_liquidation:
                                self.stdout.write(f'  Prix liquidation: {prix_liquidation} DH')
                            if is_upsell:
                                self.stdout.write(f'  Article Upsell active')
                          
                            # Calculer le nombre de variantes pour cet article
                            nb_variantes_article = len(couleurs) * len(pointures)
                            self.stdout.write(f'  VARIANTES: {len(couleurs)} couleurs × {len(pointures)} pointures = {nb_variantes_article} variantes')
                            
                            # Afficher les variantes qui seraient créées (si verbose activé)
                            if verbose_colors or verbose_pointures:
                                for couleur in couleurs:
                                    for pointure in pointures:
                                        self.stdout.write(f'    Variante: {couleur} - {pointure}')
                            
                            articles_created += 1
                            variantes_created += nb_variantes_article
                            continue

                        # Créer ou mettre à jour l'article
                        if article_existant:
                            # Mise à jour
                            article_existant.nom = nom
                            article_existant.prix_unitaire = prix_unitaire
                            article_existant.prix_achat = prix_achat
                            article_existant.prix_actuel = prix_unitaire
                            article_existant.categorie = categorie_obj
                            article_existant.genre = genre_obj
                            article_existant.phase = phase
                            article_existant.description = description
                            article_existant.image_url = image_url
                            
                            # Nouveaux champs upsell
                            article_existant.isUpsell = is_upsell
                            article_existant.prix_upsell_1 = prix_upsell_1
                            article_existant.prix_upsell_2 = prix_upsell_2
                            article_existant.prix_upsell_3 = prix_upsell_3
                            article_existant.prix_upsell_4 = prix_upsell_4
                            article_existant.Prix_liquidation = prix_liquidation
                            
                            # Mettre à jour modele uniquement si non conflictuel
                            if modele is not None:
                                # Si un autre article a déjà ce modele, ne pas l'écraser
                                if not Article.objects.filter(modele=modele).exclude(pk=article_existant.pk).exists():
                                    article_existant.modele = modele
                            
                            article_existant.date_modification = timezone.now()
                            article_existant.save()
                            
                            # Générer automatiquement la référence si elle n'est pas définie ou si régénération forcée
                            if (not article_existant.reference or regenerate_references) and article_existant.categorie and article_existant.genre and article_existant.modele:
                                reference_auto = article_existant.generer_reference_automatique()
                                if reference_auto:
                                    ancienne_ref = article_existant.reference
                                    article_existant.reference = reference_auto
                                    article_existant.save()
                                    if ancienne_ref and regenerate_references:
                                        self.stdout.write(f'REGENERATION: Reference regeneree: {ancienne_ref} -> {reference_auto}')
                                    else:
                                        self.stdout.write(f'REFERENCE: Reference generee automatiquement (mise a jour): {reference_auto}')
                            
                            articles_updated += 1
                            self.stdout.write(f'Article mis a jour: {nom}')
                            
                            # Supprimer les anciennes variantes pour les recréer
                            VarianteArticle.objects.filter(article=article_existant).delete()
                            
                        else:
                            # Création
                            # Éviter les collisions sur le champ unique `modele`
                            if modele is not None and Article.objects.filter(modele=modele).exists():
                                modele_to_use = None
                                self.stdout.write(f'ATTENTION: Modele {modele} deja existant, reference non definie pour {reference}')
                            else:
                                modele_to_use = modele
                            
                            article = Article.objects.create(
                                nom=nom,
                                reference=reference if reference else None,
                                modele=modele_to_use,
                                prix_unitaire=prix_unitaire,
                                prix_achat=prix_achat,
                                prix_actuel=prix_unitaire,
                                categorie=categorie_obj,
                                genre=genre_obj,
                                phase=phase,
                                description=description,
                                image_url=image_url,
                                
                                # Nouveaux champs upsell
                                isUpsell=is_upsell,
                                prix_upsell_1=prix_upsell_1,
                                prix_upsell_2=prix_upsell_2,
                                prix_upsell_3=prix_upsell_3,
                                prix_upsell_4=prix_upsell_4,
                                Prix_liquidation=prix_liquidation
                            )
                            
                            # Générer automatiquement la référence si elle n'est pas définie ou si régénération forcée
                            if (not article.reference or regenerate_references) and article.categorie and article.genre and article.modele:
                                reference_auto = article.generer_reference_automatique()
                                if reference_auto:
                                    ancienne_ref = article.reference
                                    article.reference = reference_auto
                                    article.save()
                                    if ancienne_ref and regenerate_references:
                                        self.stdout.write(f'REGENERATION: Reference regeneree: {ancienne_ref} -> {reference_auto}')
                                    else:
                                        self.stdout.write(f'REFERENCE: Reference generee automatiquement: {reference_auto}')
                            
                            articles_created += 1
                            self.stdout.write(f'CREE: Article créé: {nom}')

                        # Créer les variantes pour toutes les combinaisons couleur/pointure
                        article_to_use = article_existant if article_existant else article
                        variantes_created_for_article = 0
                        
                        # Afficher le nombre de variantes qui seront créées (pour tous les modes)
                        nb_variantes_article = len(couleurs) * len(pointures)
                        if dry_run:
                            self.stdout.write(f'  VARIANTES: {len(couleurs)} couleurs × {len(pointures)} pointures = {nb_variantes_article} variantes')
                        
                        for couleur in couleurs:
                            for pointure in pointures:
                                try:
                                    # Créer ou récupérer la couleur
                                    couleur_obj, created = Couleur.objects.get_or_create(
                                        nom=couleur,
                                        defaults={'actif': True}
                                    )
                                    
                                    # Créer ou récupérer la pointure
                                    pointure_obj, created = Pointure.objects.get_or_create(
                                        pointure=pointure,
                                        defaults={'actif': True, 'ordre': int(pointure) if pointure.isdigit() else 0}
                                    )
                                    
                                    # Créer la variante
                                    variante = VarianteArticle.objects.create(
                                        article=article_to_use,
                                        couleur=couleur_obj,
                                        pointure=pointure_obj,
                                        qte_disponible=0,  # Valeur par défaut
                                        actif=True
                                    )
                                    
                                    # Générer automatiquement la référence de la variante
                                    reference_variante_auto = variante.generer_reference_variante_automatique()
                                    if reference_variante_auto:
                                        variante.reference_variante = reference_variante_auto
                                        variante.save()
                                        if verbose_colors:
                                            self.stdout.write(f'  VARIANTES: Reference variante generee: {reference_variante_auto}')
                                    
                                    variantes_created_for_article += 1
                                    
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.ERROR(f'ERREUR: Erreur lors de la création de la variante {couleur}-{pointure}: {str(e)}')
                                    )
                        
                        variantes_created += variantes_created_for_article
                        
                        # Afficher le progrès
                        if (articles_created + articles_updated) % 10 == 0:
                            self.stdout.write(f'PROGRES: Articles traites: {articles_created + articles_updated + articles_skipped}')

                    except Exception as e:
                        error_msg = f'Ligne {row_num}: Erreur lors du traitement - {str(e)}'
                        self.stdout.write(self.style.ERROR(f'ERREUR: {error_msg}'))
                        errors.append(error_msg)

                # Résumé final
                self.stdout.write('\n' + '='*60)
                self.stdout.write('RESUME DE L\'IMPORTATION')
                self.stdout.write('='*60)
                
                if dry_run:
                    self.stdout.write(f'CREE: Articles qui seraient crees: {articles_created}')
                    self.stdout.write(f'MISE A JOUR: Articles qui seraient mis a jour: {articles_updated}')
                    self.stdout.write(f'IGNORE: Articles ignores: {articles_skipped}')
                    self.stdout.write(f'VARIANTES: Variantes qui seraient creees: {variantes_created}')
                    
                    # Statistiques détaillées des variantes
                    if articles_created + articles_updated > 0:
                        moy_variantes = variantes_created / (articles_created + articles_updated)
                        self.stdout.write(f'STATS: Moyenne de variantes par article: {moy_variantes:.1f}')
                        self.stdout.write(f'STATS: Ratio variantes/articles: {variantes_created}:{articles_created + articles_updated}')
                else:
                    self.stdout.write(f'CREE: Articles crees: {articles_created}')
                    self.stdout.write(f'MISE A JOUR: Articles mis a jour: {articles_updated}')
                    self.stdout.write(f'IGNORE: Articles ignores: {articles_skipped}')
                    self.stdout.write(f'VARIANTES: Variantes creees: {variantes_created}')
                    
                    # Statistiques détaillées des variantes
                    if articles_created + articles_updated > 0:
                        moy_variantes = variantes_created / (articles_created + articles_updated)
                        self.stdout.write(f'STATS: Moyenne de variantes par article: {moy_variantes:.1f}')
                        self.stdout.write(f'STATS: Ratio variantes/articles: {variantes_created}:{articles_created + articles_updated}')

                # Statistiques additionnelles
                if not dry_run:
                    total_articles = Article.objects.count()
                    articles_upsell = Article.objects.filter(isUpsell=True).count()
                    articles_liquidation = Article.objects.filter(Prix_liquidation__isnull=False).count()
                    
                    self.stdout.write(f'\nSTATS: STATISTIQUES GLOBALES:')
                    self.stdout.write(f'TOTAL: Total articles en base: {total_articles}')
                    self.stdout.write(f'UPSELL: Articles avec upsell: {articles_upsell}')
                    self.stdout.write(f'LIQUIDATION: Articles avec prix liquidation: {articles_liquidation}')

                if errors:
                    self.stdout.write(f'\nERREUR: Erreurs rencontrees: {len(errors)}')
                    for error in errors[:5]:  # Afficher les 5 premières erreurs
                        self.stdout.write(f'  - {error}')
                    if len(errors) > 5:
                        self.stdout.write(f'  ... et {len(errors) - 5} autres erreurs')

                self.stdout.write('\nOK: Import termine avec succes!')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'FATAL: Erreur lors de la lecture du fichier CSV: {str(e)}')
            )

    def _parse_price(self, price_str):
        """Parse un prix depuis le CSV et le convertit en Decimal (robuste)."""
        if price_str is None:
            return None
        s = str(price_str)
        # Normaliser et nettoyer des artefacts courants
        s = s.replace('\xa0', ' ').replace('DH', '').replace('DHS', '').replace('MAD', '')
        s = s.strip()
        if s == '' or s == '0' or s == '0.00':
            return None
        # Extraire la première occurrence numérique (ex: 1.234,56 -> 1.234,56)
        match = re.search(r'[+-]?\d{1,3}(?:[\s\u00A0\.]\d{3})*(?:[\.,]\d+)?|[+-]?\d+(?:[\.,]\d+)?', s)
        if not match:
            return None
        num = match.group(0)
        # Retirer séparateurs de milliers (espace, NBSP, point) quand une virgule ou un point décimal est utilisé
        num = num.replace('\u00A0', ' ').replace(' ', '')
        # Si les deux séparateurs existent, on considère la dernière occurrence comme décimale
        if ',' in num and '.' in num:
            # Supposer format européen (1.234,56)
            num = num.replace('.', '').replace(',', '.')
        else:
            # Un seul séparateur -> remplacer virgule par point
            num = num.replace(',', '.')
        try:
            return Decimal(num)
        except (InvalidOperation, ValueError, TypeError):
            return None

    def _extract_modele(self, reference):
        """Extrait le numéro de modèle de la référence (ex: YZ478 -> 478, CHAUSS FEMYZ900 -> 900)"""
        if not reference:
            return None
        
        # Nettoyer la référence en retirant les espaces
        reference_clean = str(reference).replace(' ', '').upper()
        
        # Chercher le pattern YZ suivi de chiffres (même si collé à d'autres lettres)
        match = re.search(r'YZ(\d+)', reference_clean)
        if match:
            try:
                modele_num = int(match.group(1))
                return modele_num
            except (ValueError, TypeError):
                return None
        
        # Si pas de pattern YZ trouvé, chercher juste des chiffres à la fin
        match = re.search(r'(\d+)$', reference_clean)
        if match:
            try:
                modele_num = int(match.group(1))
                return modele_num
            except (ValueError, TypeError):
                return None
        
        return None

    def _parse_pointures(self, pointures_str, verbose=False):
        """Parse les pointures depuis le CSV avec création d'intervalle complet"""
        if not pointures_str or pointures_str.strip() == '':
            if verbose:
                self.stdout.write(f'  POINTURES: Aucune pointure specifiee, utilise par defaut: Standard')
            return ['Standard']  # Pointure par défaut
        
        pointures = []
        pointures_str = pointures_str.strip()
        
        # Parser les pointures avec différents formats
        # Format 1: "37---41" ou "37--41" ou "37-41" (intervalle avec tirets)
        if '---' in pointures_str:
            parts = pointures_str.split('---')
        elif '--' in pointures_str:
            parts = pointures_str.split('--')
        elif '-' in pointures_str and not pointures_str.startswith('-'):
            parts = pointures_str.split('-')
        else:
            parts = [pointures_str]
        
        if len(parts) >= 2:
            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                
                # Créer l'intervalle complet avec incrémentation de 1
                if start <= end:
                    pointures = [str(i) for i in range(start, end + 1)]
                    if verbose:
                        self.stdout.write(f'  POINTURES: Intervalle cree: {start} a {end} -> {pointures}')
                else:
                    # Si start > end, inverser l'ordre
                    pointures = [str(i) for i in range(end, start + 1)]
                    if verbose:
                        self.stdout.write(f'  POINTURES: Intervalle inverse cree: {end} a {start} -> {pointures}')
                    
            except (ValueError, IndexError):
                # Si pas d'intervalle valide, traiter comme pointures individuelles
                pointures = [pointures_str]
                if verbose:
                    self.stdout.write(f'  POINTURES: Format invalide, utilise comme pointure unique: {pointures_str}')
        else:
            # Pointures séparées par des virgules, espaces ou autres séparateurs
            if ',' in pointures_str:
                pointures = [p.strip() for p in pointures_str.split(',') if p.strip()]
            elif ' ' in pointures_str:
                pointures = [p.strip() for p in pointures_str.split(' ') if p.strip()]
            else:
                pointures = [pointures_str]
            
            if verbose:
                self.stdout.write(f'  POINTURES: Pointures individuelles detectees: {pointures}')
        
        # Filtrer les pointures vides et valider qu'elles sont numériques
        pointures_finales = []
        for p in pointures:
            if p and p.strip() and p.strip() != '':
                # Vérifier si c'est un nombre valide
                try:
                    int(p.strip())
                    pointures_finales.append(p.strip())
                except ValueError:
                    # Si ce n'est pas un nombre, l'ajouter quand même (ex: "Standard", "XL", etc.)
                    pointures_finales.append(p.strip())
        
        # Si aucune pointure valide trouvée, retourner une pointure par défaut
        if not pointures_finales:
            pointures_finales = ['Standard']
            if verbose:
                self.stdout.write(f'  POINTURES: Aucune pointure valide, utilise par defaut: Standard')
        
        return pointures_finales

    def _parse_couleurs(self, couleurs_str):
        """Parse les couleurs depuis le CSV avec normalisation de la casse"""
        if not couleurs_str or couleurs_str.strip() == '' or couleurs_str.strip() == '--':
            return ['Standard']  # Couleur par défaut si aucune spécifiée
        
        # Mapping des couleurs communes pour normaliser la casse
        couleur_mapping = {
            'NOIR': 'Noir',
            'BLANC': 'Blanc',
            'ROUGE': 'Rouge',
            'BLEU': 'Bleu',
            'VERT': 'Vert',
            'JAUNE': 'Jaune',
            'ROSE': 'Rose',
            'VIOLET': 'Violet',
            'ORANGE': 'Orange',
            'GRIS': 'Gris',
            'MARRON': 'Marron',
            'BEIGE': 'Beige',
            'CAMEL': 'Camel',
            'BRONZE': 'Bronze',
            'DORE': 'Doré',
            'ARGENT': 'Argent',
            'GOLD': 'Doré',
            'SILVER': 'Argent',
            'NAVY': 'Bleu Marine',
            'NUDE': 'Nude',
            'KAKI': 'Kaki',
            'TURQUOISE': 'Turquoise',
            'FUCHSIA': 'Fuchsia',
            'LIME': 'Lime',
            'CORAIL': 'Corail',
            'SAUMON': 'Saumon',
            'BORDEAUX': 'Bordeaux',
            'PRUNE': 'Prune',
            'TAUPE': 'Taupe',
            'ECRU': 'Ecru',
            'IVOIRE': 'Ivoire',
            'CREME': 'Crème',
            'MULTICOLORE': 'Multicolore',
            'LEOPARD': 'Léopard',
            'ZEBRE': 'Zèbre',
            'PYTHON': 'Python',
            'CROCO': 'Croco',
            'METAL': 'Métallisé',
            'METALLISE': 'Métallisé',
            'BRILLANT': 'Brillant',
            'MAT': 'Mat',
            'SATINE': 'Satiné',
            'BLEU JEANS': 'Bleu Jeans',
            'BLEU JEAN': 'Bleu Jeans',
            'BLANC GRIS': 'Blanc Gris',
            'GRENAT': 'Grenat',
            'COGNAC': 'Cognac'
        }
        
        couleurs = []
        # Nettoyer la chaîne (retirer les retours à la ligne et espaces en trop)
        couleurs_clean = str(couleurs_str).replace('\n', ' ').replace('\r', ' ')
        couleurs_clean = re.sub(r'\s+', ' ', couleurs_clean).strip()
        
        # Parser les couleurs (séparées par des tirets, virgules, slashes ou pipes)
        separateurs = ['-', ',', '/', '|', ';']
        couleurs_brutes = [couleurs_clean]
        
        for sep in separateurs:
            if sep in couleurs_clean:
                couleurs_brutes = [c.strip() for c in couleurs_clean.split(sep) if c.strip() and c.strip() != '']
                break
        
        # Nettoyer chaque couleur et normaliser la casse
        couleurs_finales = []
        for couleur in couleurs_brutes:
            couleur_clean = couleur.strip().upper()
            if couleur_clean and couleur_clean != '--' and len(couleur_clean) > 0:
                # Vérifier si la couleur existe dans le mapping
                if couleur_clean in couleur_mapping:
                    couleur_normalisee = couleur_mapping[couleur_clean]
                else:
                    # Si pas dans le mapping, utiliser la forme title (première lettre majuscule)
                    couleur_normalisee = couleur.strip().title()
                    # Correction pour les mots composés
                    couleur_normalisee = couleur_normalisee.replace(' De ', ' de ')
                    couleur_normalisee = couleur_normalisee.replace(' Du ', ' du ')
                    couleur_normalisee = couleur_normalisee.replace(' Le ', ' le ')
                    couleur_normalisee = couleur_normalisee.replace(' La ', ' la ')
                
                couleurs_finales.append(couleur_normalisee)
        
        # Si aucune couleur valide trouvée, retourner une couleur par défaut
        if not couleurs_finales:
            couleurs_finales = ['Standard']
        
        # Supprimer les doublons tout en préservant l'ordre
        couleurs_uniques = []
        for couleur in couleurs_finales:
            if couleur not in couleurs_uniques:
                couleurs_uniques.append(couleur)
            
        return couleurs_uniques