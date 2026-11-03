from django.db import models

# Create your models here.
class Transporteur(models.Model):
    code = models.SlugField(max_length=40, unique=True)
    nom = models.CharField(max_length=80)
    class Meta:
        ordering = ["nom"]
    def __str__(self):
        return self.nom
    
    
class Entrepot(models.Model):
    code = models.SlugField(max_length=40, unique=True)
    nom = models.CharField(max_length=80)
    class Meta:
        ordering = ["nom"]
    def __str__(self):
        return self.nom
    
    
class Commande(models.Model):
    class Statut(models.TextChoices):
        COMPLETE = "COMPLETE"
        CLOSED = "CLOSED"
        PENDING = "PENDING"
        PENDING_PAYMENT = "PENDING_PAYMENT"
        PROCESSING = "PROCESSING"
        ON_HOLD = "ON_HOLD"
        PAYMENT_REVIEW = "PAYMENT_REVIEW"
        CANCELED = "CANCELED"
        SUSPECTED_FRAUD = "SUSPECTED_FRAUD"
    order_id = models.PositiveIntegerField(unique=True)
    date_commande = models.DateTimeField(db_index=True)
    statut = models.CharField(max_length=20, choices=Statut.choices)
    client_id = models.PositiveIntegerField(db_index=True)
    segment_client = models.CharField(max_length=30)
    marche = models.CharField(max_length=30, db_index=True)
    region = models.CharField(max_length=60, db_index=True)
    pays = models.CharField(max_length=80)
    ville = models.CharField(max_length=80, blank=True)
    nb_lignes_commande = models.PositiveIntegerField(default=0)
    nb_articles = models.PositiveIntegerField()
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    profit_total = models.DecimalField(max_digits=12, decimal_places=2)
    class Meta:
        ordering = ["-date_commande"]
    def __str__(self):
        return f"Commande {self.order_id}"


class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="lignes_commande")
    order_item_id = models.PositiveBigIntegerField(unique=True)
    product_card_id = models.PositiveIntegerField()
    product_name = models.CharField(max_length=255, blank=True)
    category_name = models.CharField(max_length=255, blank=True)
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    remise = models.DecimalField(max_digits=12, decimal_places=2)
    taux_remise = models.DecimalField(max_digits=12, decimal_places=6)
    ratio_profit = models.DecimalField(max_digits=12, decimal_places=6)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    profit = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["order_item_id"]

    def __str__(self):
        return f"Ligne {self.order_item_id} de {self.commande}"
    
    
class Expedition(models.Model):
    class StatutLivraison(models.TextChoices):
        A_TEMPS = "a_temps", "À temps"
        EN_AVANCE = "en_avance", "En avance"
        EN_RETARD = "en_retard", "En retard"
        ANNULEE = "annulee", "Annulée"
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE, related_name="expedition")
    transporteur = models.ForeignKey(Transporteur, on_delete=models.PROTECT, related_name="expeditions")
    entrepot = models.ForeignKey(Entrepot, on_delete=models.PROTECT, related_name="expeditions")
    date_expedition = models.DateTimeField(null=True, blank=True)
    delai_prevu_jours = models.PositiveSmallIntegerField()
    delai_reel_jours = models.PositiveSmallIntegerField()
    ecart_jours = models.SmallIntegerField(help_text="délai réel - délai prévu (négatif = en avance)")
    statut_livraison = models.CharField(max_length=12, choices=StatutLivraison.choices, db_index=True)
    en_retard = models.BooleanField(db_index=True)
    cout_estime = models.DecimalField(max_digits=10, decimal_places=2, help_text="Coût estimé")

    class Meta:
        indexes = [
            models.Index(fields=["transporteur", "en_retard"]),
            models.Index(fields=["entrepot", "en_retard"]),
            models.Index(fields=["statut_livraison", "transporteur"]),
        ]
        
    def __str__(self):
        return f"Expédition de {self.commande}"


class EtlRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running"
        SUCCESS = "success"
        FAILED = "failed"
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RUNNING)
    source_file = models.CharField(max_length=255)
    rows_read = models.PositiveIntegerField(default=0)
    rows_rejected = models.PositiveIntegerField(default=0)
    commandes_loaded = models.PositiveIntegerField(default=0)
    expeditions_loaded = models.PositiveIntegerField(default=0)
    lignes_commande_loaded = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)
    
    class Meta:
        ordering = ["-started_at"]