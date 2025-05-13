from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Maintenance(models.Model):
    _name = 'it.parc.maintenance'
    _description = 'Intervention de maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_debut desc'
    
    name = fields.Char(string='Référence', required=True, tracking=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('it.parc.maintenance'))
    
    type = fields.Selection([
        ('preventive', 'Préventive'),
        ('corrective', 'Corrective'),
        ('installation', 'Installation'),
        ('mise_a_jour', 'Mise à jour'),
        ('autre', 'Autre')
    ], string='Type d\'intervention', required=True, tracking=True)
    
    etat = fields.Selection([
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée')
    ], string='État', default='planifiee', tracking=True)
    
    date_debut = fields.Datetime(string='Date de début', required=True, default=fields.Datetime.now, tracking=True)
    date_fin = fields.Datetime(string='Date de fin', tracking=True)
    duree = fields.Float(string='Durée (heures)', compute='_compute_duree', store=True)
    
    description = fields.Text(string='Description', tracking=True)
    actions_realisees = fields.Text(string='Actions réalisées', tracking=True)
    resultats = fields.Text(string='Résultats', tracking=True)
    notes = fields.Text(string='Notes techniques', tracking=True)
    
    client_id = fields.Many2one('it.parc.client', string='Client', required=True, tracking=True)
    materiel_id = fields.Many2one('it.parc.materiel', string='Matériel concerné', tracking=True)
    incident_id = fields.Many2one('it.parc.incident', string='Incident associé', tracking=True)
    ticket_id = fields.Many2one('it.parc.ticket', string='Ticket associé', tracking=True)
    
    facturable = fields.Boolean(string='Facturable', default=False, tracking=True)
    tarif_horaire = fields.Float(string='Tarif horaire', tracking=True)
    montant_estime = fields.Float(string='Montant estimé', compute='_compute_montant_estime', store=True)
    facture_ids = fields.Many2many('it.parc.facturation', string='Factures associées')
    
    @api.depends('date_debut', 'date_fin')
    def _compute_duree(self):
        for maintenance in self:
            if maintenance.date_debut and maintenance.date_fin:
                delta = maintenance.date_fin - maintenance.date_debut
                maintenance.duree = delta.total_seconds() / 3600
            else:
                maintenance.duree = 0
    
    @api.depends('duree', 'tarif_horaire', 'facturable')
    def _compute_montant_estime(self):
        for maintenance in self:
            if maintenance.facturable and maintenance.duree and maintenance.tarif_horaire:
                maintenance.montant_estime = maintenance.duree * maintenance.tarif_horaire
            else:
                maintenance.montant_estime = 0
    
    def action_demarrer(self):
        self.ensure_one()
        self.write({
            'etat': 'en_cours',
            'date_debut': fields.Datetime.now()
        })
    
    def action_terminer(self):
        self.ensure_one()
        self.write({
            'etat': 'terminee',
            'date_fin': fields.Datetime.now()
        })
        
        # Si lié à un incident, proposer de le résoudre
        if self.incident_id and self.incident_id.etat != 'resolu':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Résoudre l\'incident ?',
                'view_mode': 'form',
                'res_model': 'it.parc.incident',
                'res_id': self.incident_id.id,
                'target': 'new',
                'context': {'default_etat': 'resolu', 'default_date_cloture': fields.Datetime.now()}
            }
    
    def action_annuler(self):
        self.ensure_one()
        self.etat = 'annulee'

    def action_view_factures(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factures',
            'view_mode': 'list,form',
            'res_model': 'it.parc.facturation',
            'domain': [('id', 'in', self.facture_ids.ids)],
            'context': {'default_client_id': self.client_id.id},
        }

class MaintenancePreventive(models.Model):
    _name = 'it.parc.maintenance.preventive'
    _description = 'Plan de maintenance préventive'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Référence', required=True, tracking=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('it.parc.maintenance.preventive'))
    
    categorie_id = fields.Many2one('it.parc.materiel.categorie', string='Catégorie de matériel', required=True, tracking=True)
    client_id = fields.Many2one('it.parc.client', string='Client', tracking=True)
    
    frequence = fields.Selection([
        ('mensuelle', 'Mensuelle'),
        ('trimestrielle', 'Trimestrielle'),
        ('semestrielle', 'Semestrielle'),
        ('annuelle', 'Annuelle')
    ], string='Fréquence', default='trimestrielle', required=True, tracking=True)
    
    date_derniere = fields.Date(string='Dernière maintenance', tracking=True)
    date_prochaine = fields.Date(string='Prochaine maintenance', compute='_compute_date_prochaine', store=True)
    
    description = fields.Text(string='Description des tâches', tracking=True, 
                             help="Décrivez les tâches à effectuer lors de cette maintenance")
    
    active = fields.Boolean(default=True)
    
    @api.depends('date_derniere', 'frequence')
    def _compute_date_prochaine(self):
        for plan in self:
            if not plan.date_derniere:
                plan.date_prochaine = fields.Date.today()
                continue
                
            if plan.frequence == 'mensuelle':
                plan.date_prochaine = plan.date_derniere + relativedelta(months=1)
            elif plan.frequence == 'trimestrielle':
                plan.date_prochaine = plan.date_derniere + relativedelta(months=3)
            elif plan.frequence == 'semestrielle':
                plan.date_prochaine = plan.date_derniere + relativedelta(months=6)
            elif plan.frequence == 'annuelle':
                plan.date_prochaine = plan.date_derniere + relativedelta(years=1)
    
    def action_generer_maintenances(self):
        """Génère les interventions de maintenance préventive planifiées"""
        today = fields.Date.today()
        plans = self.search([
            ('date_prochaine', '<=', today),
            ('active', '=', True)
        ])
        
        for plan in plans:
            # Trouver les matériels concernés
            domain = [('categorie_id', '=', plan.categorie_id.id)]
            if plan.client_id:
                domain.append(('client_id', '=', plan.client_id.id))
            materiels = self.env['it.parc.materiel'].search(domain)
            
            for materiel in materiels:
                # Créer une intervention de maintenance pour chaque matériel
                self.env['it.parc.maintenance'].create({
                    'type': 'preventive',
                    'client_id': materiel.client_id.id,
                    'materiel_id': materiel.id,
                    'description': f"Maintenance préventive planifiée: {plan.description or ''}",
                    'date_debut': fields.Datetime.now(),
                    'facturable': False,
                })
            
            # Mettre à jour la date de dernière maintenance
            plan.date_derniere = today


