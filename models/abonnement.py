from odoo import models, fields, api
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

class Abonnement(models.Model):
    _name = 'it.parc.abonnement'
    _description = 'Abonnement & Facturation récurrente'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'prochaine_facturation asc'
    
    name = fields.Char(string='Référence', required=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('it.parc.abonnement'))
    active = fields.Boolean(default=True, tracking=True)
    
    # Relations
    contrat_id = fields.Many2one('it.parc.contrat', string='Contrat lié', required=True, tracking=True,
                                domain="[('etat', '=', 'actif')]")
    client_id = fields.Many2one('it.parc.client', string='Client', required=True, tracking=True)
    
    # Informations de facturation
    frequence = fields.Selection([
        ('mensuelle', 'Mensuelle'),
        ('bimensuelle', 'Tous les 2 mois'),
        ('trimestrielle', 'Trimestrielle'),
        ('semestrielle', 'Semestrielle'),
        ('annuelle', 'Annuelle')
    ], string='Fréquence', required=True, default='mensuelle', tracking=True)
    
    date_debut = fields.Date(string='Date de début', required=True, tracking=True)
    date_fin = fields.Date(string='Date de fin', tracking=True)
    prochaine_facturation = fields.Date(string='Prochaine facturation', compute='_compute_prochaine_facturation', 
                                     store=True, tracking=True)
    jours_avant_notification = fields.Integer(string='Notification (jours avant)', default=7, 
                                           help="Nombre de jours avant la facturation pour envoyer une notification")
    jour_facturation = fields.Integer(string='Jour de facturation', default=1,
                                   help="Jour du mois pour la facturation (1-28)")
    
    # Mode de paiement
    mode_paiement = fields.Selection([
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('cb', 'Carte bancaire'),
        ('especes', 'Espèces'),
        ('prelevement', 'Prélèvement')
    ], string='Mode de paiement', tracking=True)
    
    # Montants et informations financières
    montant_ht = fields.Float(string='Montant HT', required=True, tracking=True)
    taux_tva = fields.Float(string='Taux TVA (%)', default=20.0, tracking=True)
    montant_tva = fields.Float(string='Montant TVA', compute='_compute_montants', store=True)
    montant_ttc = fields.Float(string='Montant TTC', compute='_compute_montants', store=True)
    devise = fields.Selection([
        ('eur', 'EUR (€)'),
        ('usd', 'USD ($)'),
        ('mad', 'MAD (DH)'),
    ], string='Devise', default='eur', tracking=True)
    
    # Articles et descriptions
    description = fields.Text(string='Description', tracking=True)
    ligne_ids = fields.One2many('it.parc.abonnement.ligne', 'abonnement_id', string='Articles')
    
    # Statut de l'abonnement
    etat = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('actif', 'Actif'),
        ('suspendu', 'Suspendu'),
        ('termine', 'Terminé')
    ], string='État', default='brouillon', tracking=True)
    
    # Historique des factures
    facture_ids = fields.One2many('it.parc.facturation', 'abonnement_id', string='Factures générées')
    facture_count = fields.Integer(compute='_compute_facture_count', string='Nombre de factures')
    total_facture = fields.Float(compute='_compute_facture_count', string='Total facturé')
    
    # Email pour notifications
    email_notification = fields.Char(string='Email pour notifications', tracking=True)
    
    @api.depends('facture_ids')
    def _compute_facture_count(self):
        for abonnement in self:
            factures = abonnement.facture_ids
            abonnement.facture_count = len(factures)
            abonnement.total_facture = sum(facture.montant_ttc for facture in factures)
    
    @api.depends('montant_ht', 'taux_tva')
    def _compute_montants(self):
        for abonnement in self:
            abonnement.montant_tva = abonnement.montant_ht * (abonnement.taux_tva / 100.0)
            abonnement.montant_ttc = abonnement.montant_ht + abonnement.montant_tva
    
    @api.depends('date_debut', 'frequence', 'jour_facturation', 'facture_ids', 'etat')
    def _compute_prochaine_facturation(self):
        today = fields.Date.today()
        
        for abonnement in self:
            # Si l'abonnement n'est pas actif, pas de prochaine facturation
            if abonnement.etat != 'actif':
                abonnement.prochaine_facturation = False
                continue
            
            # Si date de fin définie et dépassée, pas de prochaine facturation
            if abonnement.date_fin and abonnement.date_fin < today:
                abonnement.prochaine_facturation = False
                continue
            
            # Trouver la dernière facture
            derniere_facture = self.env['it.parc.facturation'].search([
                ('abonnement_id', '=', abonnement.id),
                ('etat', 'not in', ['annulee'])
            ], order='date desc', limit=1)
            
            # Déterminer la date de début pour calcul
            date_base = derniere_facture.date if derniere_facture else abonnement.date_debut
            
            # Ajuster au jour de facturation souhaité si possible
            if isinstance(date_base, date):
                # Convertir en datetime pour manipulations
                date_base_dt = datetime.combine(date_base, datetime.min.time())
                
                # Calculer la prochaine date de facturation en fonction de la fréquence
                if abonnement.frequence == 'mensuelle':
                    next_date = date_base_dt + relativedelta(months=1)
                elif abonnement.frequence == 'bimensuelle':
                    next_date = date_base_dt + relativedelta(months=2)
                elif abonnement.frequence == 'trimestrielle':
                    next_date = date_base_dt + relativedelta(months=3)
                elif abonnement.frequence == 'semestrielle':
                    next_date = date_base_dt + relativedelta(months=6)
                elif abonnement.frequence == 'annuelle':
                    next_date = date_base_dt + relativedelta(years=1)
                else:
                    next_date = date_base_dt + relativedelta(months=1)
                
                # Ajuster au jour du mois souhaité si possible
                jour = min(abonnement.jour_facturation, 28)  # Limiter à 28 pour éviter les problèmes avec février
                next_date = next_date.replace(day=jour)
                
                # Convertir en date
                abonnement.prochaine_facturation = next_date.date()
            else:
                # Fallback au cas où
                abonnement.prochaine_facturation = fields.Date.today() + timedelta(days=30)
    
    @api.onchange('contrat_id')
    def _onchange_contrat_id(self):
        if self.contrat_id:
            self.client_id = self.contrat_id.client_id.id
            self.montant_ht = self.contrat_id.montant
            self.devise = self.contrat_id.devise
            self.frequence = self.contrat_id.frequence_facturation
            self.description = f"Abonnement pour le contrat {self.contrat_id.name} - {self.contrat_id.type}"
    
    def action_activer(self):
        self.ensure_one()
        self.etat = 'actif'
    
    def action_suspendre(self):
        self.ensure_one()
        self.etat = 'suspendu'
    
    def action_terminer(self):
        self.ensure_one()
        self.etat = 'termine'
    
    def action_generer_facture(self):
        """Génère une facture manuellement"""
        self.ensure_one()
        facture_vals = self._prepare_facture_vals()
        facture = self.env['it.parc.facturation'].create(facture_vals)
        
        # Créer les lignes de facture si nécessaire
        if self.ligne_ids:
            for ligne in self.ligne_ids:
                ligne._create_facture_ligne(facture)
        
        # Mettre à jour la prochaine date de facturation
        self._compute_prochaine_facturation()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'it.parc.facturation',
            'view_mode': 'form',
            'res_id': facture.id,
            'target': 'current',
        }
    
    def _prepare_facture_vals(self):
        """Prépare les valeurs pour créer une facture"""
        today = fields.Date.today()
        
        # Déterminer la période de facturation pour la description
        debut_periode = self.prochaine_facturation or today
        fin_periode = False
        
        if self.frequence == 'mensuelle':
            fin_periode = debut_periode + relativedelta(months=1, days=-1)
        elif self.frequence == 'bimensuelle':
            fin_periode = debut_periode + relativedelta(months=2, days=-1)
        elif self.frequence == 'trimestrielle':
            fin_periode = debut_periode + relativedelta(months=3, days=-1)
        elif self.frequence == 'semestrielle':
            fin_periode = debut_periode + relativedelta(months=6, days=-1)
        elif self.frequence == 'annuelle':
            fin_periode = debut_periode + relativedelta(years=1, days=-1)
        
        description = self.description or f"Abonnement {self.name} - Période: {debut_periode} au {fin_periode}"
        
        return {
            'client_id': self.client_id.id,
            'contrat_id': self.contrat_id.id,
            'abonnement_id': self.id,
            'date': today,
            'echeance': today + timedelta(days=30),  # Échéance à 30 jours par défaut
            'montant_ht': self.montant_ht,
            'taux_tva': self.taux_tva,
            'devise': self.devise,
            'description': description,
            'etat': 'brouillon',
            'mode_paiement': self.mode_paiement,
        }
    
    def action_view_factures(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factures',
            'view_mode': 'list,form',
            'res_model': 'it.parc.facturation',
            'domain': [('abonnement_id', '=', self.id)],
            'context': {'default_abonnement_id': self.id, 'default_client_id': self.client_id.id},
        }
    
    @api.model
    def _cron_generer_factures(self):
        """Méthode CRON pour générer automatiquement les factures"""
        today = fields.Date.today()
        
        # Trouver les abonnements à facturer (date de prochaine facturation = aujourd'hui ou passée)
        abonnements_a_facturer = self.search([
            ('etat', '=', 'actif'),
            ('prochaine_facturation', '<=', today),
            '|', ('date_fin', '=', False), ('date_fin', '>=', today)
        ])
        
        factures_creees = self.env['it.parc.facturation']
        
        for abonnement in abonnements_a_facturer:
            facture_vals = abonnement._prepare_facture_vals()
            facture = self.env['it.parc.facturation'].create(facture_vals)
            factures_creees += facture
            
            # Créer les lignes de facture si nécessaire
            if abonnement.ligne_ids:
                for ligne in abonnement.ligne_ids:
                    ligne._create_facture_ligne(facture)
        
        return factures_creees
    
    @api.model
    def _cron_notification_facture(self):
        """Méthode CRON pour notifier les abonnements avant facturation"""
        today = fields.Date.today()
        
        # Trouver les abonnements qui seront facturés prochainement
        abonnements_a_notifier = self.search([
            ('etat', '=', 'actif'),
            ('email_notification', '!=', False)
        ])
        
        for abonnement in abonnements_a_notifier:
            if abonnement.prochaine_facturation:
                jours_avant = (abonnement.prochaine_facturation - today).days
                if jours_avant == abonnement.jours_avant_notification:
                    self._envoyer_notification(abonnement)
    
    def _envoyer_notification(self, abonnement):
        """Envoie une notification par email avant facturation"""
        if not abonnement.email_notification:
            return
        
        template = self.env.ref('it_parc.email_template_abonnement_notification')
        if template:
            template.send_mail(abonnement.id, force_send=True)


class AbonnementLigne(models.Model):
    _name = 'it.parc.abonnement.ligne'
    _description = 'Ligne d\'abonnement'
    _order = 'sequence, id'
    
    abonnement_id = fields.Many2one('it.parc.abonnement', string='Abonnement', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Séquence', default=10)
    
    name = fields.Char(string='Description', required=True)
    quantite = fields.Float(string='Quantité', default=1.0)
    prix_unitaire = fields.Float(string='Prix unitaire HT')
    montant = fields.Float(string='Montant HT', compute='_compute_montant', store=True)
    
    @api.depends('quantite', 'prix_unitaire')
    def _compute_montant(self):
        for ligne in self:
            ligne.montant = ligne.quantite * ligne.prix_unitaire
    
    def _create_facture_ligne(self, facture):
        """Crée une ligne de facture correspondante"""
        # Cette méthode sera appelée si vous décidez d'ajouter un modèle de ligne de facture plus tard
        # Pour l'instant, les informations sont simplement incluses dans la description de la facture
        if not facture.description:
            facture.description = ''
        
        facture.description += f"\n• {self.name}: {self.quantite} x {self.prix_unitaire} = {self.montant} {facture.devise}"