from odoo import models, fields, api
from datetime import date, timedelta

class Contrat(models.Model):
    _name = 'it.parc.contrat'
    _description = 'Contrat de maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Référence', required=True, tracking=True)
    reference = fields.Char(string='Référence interne', tracking=True)
    description = fields.Text(string='Description', tracking=True)
    date_debut = fields.Date(string='Date de début', required=True, tracking=True)
    date_fin = fields.Date(string='Date de fin', required=True, tracking=True)
    
    # Nouveaux champs pour les SLA et conditions
    sla_delai_resolution = fields.Integer(string='Délai de résolution garanti (heures)', tracking=True)
    sla_interventions_inclus = fields.Integer(string='Nombre d\'interventions incluses', tracking=True)
    sla_details = fields.Text(string='Détails des SLA', tracking=True)
    
    # Conditions de renouvellement et facturation
    frequence_facturation = fields.Selection([
        ('mensuelle', 'Mensuelle'),
        ('trimestrielle', 'Trimestrielle'),
        ('semestrielle', 'Semestrielle'),
        ('annuelle', 'Annuelle'),
        ('unique', 'Paiement unique')
    ], string='Fréquence de facturation', default='mensuelle', tracking=True)
    
    renouvellement_auto = fields.Boolean(string='Renouvellement automatique', default=False, tracking=True)
    preavis_renouvellement = fields.Integer(string='Préavis de renouvellement (jours)', default=30, tracking=True)
    condition_renouvellement = fields.Text(string='Conditions de renouvellement', tracking=True)
    
    # Tarifs hors forfait
    tarif_horaire_hf = fields.Float(string='Tarif horaire hors forfait', tracking=True)
    tarif_deplacement_hf = fields.Float(string='Coût de déplacement hors forfait', tracking=True)
    tarifs_supplementaires = fields.Text(string='Autres tarifs supplémentaires', tracking=True)
    
    # Montants
    montant = fields.Float(string='Montant forfaitaire par période', tracking=True)
    montant_total = fields.Float(string='Montant total du contrat', compute='_compute_montant_total', store=True, tracking=True)
    devise = fields.Selection([
        ('eur', 'EUR (€)'),
        ('usd', 'USD ($)'),
        ('mad', 'MAD (DH)'),
    ], string='Devise', default='eur', tracking=True)
    
    # Type de contrat étendu
    type = fields.Selection([
        ('full_support', 'Full Support'),
        ('maintenance', 'Maintenance'),
        ('materiel', 'Matériel uniquement'),
        ('licence', 'Licence uniquement'),
        ('assistance', 'Assistance'),
        ('autre', 'Autre')
    ], string='Type de contrat', required=True, tracking=True)
    
    etat = fields.Selection([
        ('draft', 'Brouillon'),
        ('en_attente', 'En attente'),
        ('actif', 'Actif'),
        ('expire', 'Expiré'),
        ('resilie', 'Résilié')
    ], string='État', default='draft', tracking=True, compute='_compute_etat', store=True)
    
    # Alerte sur renouvellement
    alerte_renouvellement = fields.Boolean(string='Alerte de renouvellement', compute='_compute_alerte_renouvellement', store=True)
    date_alerte_renouvellement = fields.Date(string='Date d\'alerte renouvellement', compute='_compute_alerte_renouvellement', store=True)
    jours_avant_echeance = fields.Integer(string='Jours avant échéance', compute='_compute_alerte_renouvellement', store=True)
    
    # Relations
    client_id = fields.Many2one('it.parc.client', string='Client', required=True, tracking=True)
    materiel_ids = fields.One2many('it.parc.materiel', 'contrat_id', string='Matériels couverts')
    facture_ids = fields.One2many('it.parc.facturation', 'contrat_id', string='Factures')
    
    # Documents attachés
    contrat_signe_ids = fields.Many2many(
        'ir.attachment',
        'contrat_attachment_rel',
        'contrat_id',
        'attachment_id',
        string='Contrat signé'
    )
    documents_annexes_ids = fields.Many2many(
        'ir.attachment',
        'contrat_docs_attachment_rel',
        'contrat_id',
        'attachment_id',
        string='Documents annexes'
    )
    
    materiel_count = fields.Integer(compute='_compute_materiel_count', string='Nombre de matériels')
    facture_count = fields.Integer(compute='_compute_facture_count', string='Nombre de factures')
    
    @api.depends('materiel_ids')
    def _compute_materiel_count(self):
        for contrat in self:
            contrat.materiel_count = len(contrat.materiel_ids)
    
    @api.depends('facture_ids')
    def _compute_facture_count(self):
        for contrat in self:
            contrat.facture_count = len(contrat.facture_ids)
    
    @api.depends('frequence_facturation', 'montant', 'date_debut', 'date_fin')
    def _compute_montant_total(self):
        for contrat in self:
            if contrat.date_debut and contrat.date_fin and contrat.montant:
                if contrat.frequence_facturation == 'unique':
                    contrat.montant_total = contrat.montant
                else:
                    delta = (contrat.date_fin - contrat.date_debut).days
                    if contrat.frequence_facturation == 'mensuelle':
                        periodes = delta / 30
                    elif contrat.frequence_facturation == 'trimestrielle':
                        periodes = delta / 90
                    elif contrat.frequence_facturation == 'semestrielle':
                        periodes = delta / 180
                    else:  # annuelle
                        periodes = delta / 365
                    
                    contrat.montant_total = contrat.montant * max(1, round(periodes))
            else:
                contrat.montant_total = 0.0
    
    @api.depends('date_debut', 'date_fin', 'preavis_renouvellement')
    def _compute_alerte_renouvellement(self):
        today = date.today()
        for contrat in self:
            if contrat.date_fin:
                jours_avant_echeance = (contrat.date_fin - today).days
                contrat.jours_avant_echeance = jours_avant_echeance
                
                # Calculer la date d'alerte en fonction du préavis
                if contrat.preavis_renouvellement:
                    date_alerte = contrat.date_fin - timedelta(days=contrat.preavis_renouvellement)
                    contrat.date_alerte_renouvellement = date_alerte
                    contrat.alerte_renouvellement = today >= date_alerte and today <= contrat.date_fin
                else:
                    contrat.date_alerte_renouvellement = False
                    contrat.alerte_renouvellement = False
            else:
                contrat.jours_avant_echeance = 0
                contrat.date_alerte_renouvellement = False
                contrat.alerte_renouvellement = False
    
    @api.depends('date_debut', 'date_fin')
    def _compute_etat(self):
        today = date.today()
        for contrat in self:
            if contrat.date_debut and contrat.date_fin:
                if contrat.date_debut > today:
                    contrat.etat = 'en_attente'
                elif contrat.date_fin < today:
                    contrat.etat = 'expire'
                else:
                    contrat.etat = 'actif'
            else:
                contrat.etat = 'draft'
    
    def action_view_materiels(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Matériels',
            'view_mode': 'list,form',
            'res_model': 'it.parc.materiel',
            'domain': [('contrat_id', '=', self.id)],
            'context': {'default_contrat_id': self.id, 'default_client_id': self.client_id.id},
        }
    
    def action_view_factures(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factures',
            'view_mode': 'list,form',
            'res_model': 'it.parc.facturation',
            'domain': [('contrat_id', '=', self.id)],
            'context': {'default_contrat_id': self.id, 'default_client_id': self.client_id.id},
        }
    
    def action_generer_facture(self):
        """Génère une facture basée sur le montant du contrat"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Générer facture',
            'view_mode': 'form',
            'res_model': 'it.parc.facturation',
            'context': {
                'default_contrat_id': self.id,
                'default_client_id': self.client_id.id,
                'default_montant_ht': self.montant,
                'default_devise': self.devise,
                'default_description': f'Facture pour le contrat {self.name} - {self.type}'
            },
            'target': 'new',
        }
    
    def action_renouveler_contrat(self):
        """Renouvelle le contrat pour une période similaire"""
        self.ensure_one()
        if self.date_fin:
            duree = (self.date_fin - self.date_debut).days
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Renouveler contrat',
                'view_mode': 'form',
                'res_model': 'it.parc.contrat',
                'context': {
                    'default_client_id': self.client_id.id,
                    'default_type': self.type,
                    'default_montant': self.montant,
                    'default_devise': self.devise,
                    'default_date_debut': self.date_fin,
                    'default_date_fin': fields.Date.from_string(self.date_fin) + timedelta(days=duree),
                    'default_description': f'Renouvellement du contrat {self.name}',
                    'default_reference': f'RENOUV-{self.reference or self.name}'
                },
                'target': 'new',
            }
    
    def action_creer_abonnement(self):
        """Créer un abonnement basé sur ce contrat"""
        self.ensure_one()
        if self.etat != 'actif':
            raise UserError("Vous ne pouvez créer un abonnement que pour un contrat actif.")
            
        # Rediriger vers le formulaire de création d'abonnement
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créer un abonnement',
            'view_mode': 'form',
            'res_model': 'it.parc.abonnement',
            'context': {
                'default_contrat_id': self.id,
                'default_client_id': self.client_id.id,
                'default_montant_ht': self.montant,
                'default_devise': self.devise,
                'default_frequence': self.frequence_facturation,
                'default_date_debut': fields.Date.today(),
                'default_description': f"Abonnement pour le contrat {self.name} - {self.type}"
            },
            'target': 'current',
        }
    
    def _cron_check_contrat_expiration(self):
        """Méthode pour le CRON qui vérifie l'expiration des contrats"""
        today = fields.Date.today()
        
        # Trouver les contrats qui expirent dans les 30 jours
        contrats_expiration = self.search([
            ('date_fin', '>=', today),
            ('date_fin', '<=', fields.Date.to_string(fields.Date.from_string(today) + timedelta(days=30))),
            ('etat', '=', 'actif')
        ])
        
        # Créer une activité pour chaque contrat
        for contrat in contrats_expiration:
            days_remaining = (contrat.date_fin - today).days
            
            # Créer une activité pour l'administrateur
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'note': f"Le contrat {contrat.name} expire dans {days_remaining} jours. Contacter le client pour un renouvellement.",
                'user_id': self.env.user.id,
                'res_id': contrat.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'it.parc.contrat')], limit=1).id,
                'date_deadline': fields.Date.today() + timedelta(days=3),
                'summary': f"Contrat {contrat.name} en expiration"
            })


