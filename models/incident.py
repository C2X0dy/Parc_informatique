from odoo import models, fields, api
from datetime import datetime

class Incident(models.Model):
    _name = 'it.parc.incident'
    _description = 'Incident informatique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_creation desc'
    
    name = fields.Char(string='Référence', required=True, tracking=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('it.parc.incident'))
    objet = fields.Char(string='Objet', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    date_creation = fields.Datetime(string='Date de création', default=fields.Datetime.now, tracking=True)
    date_cloture = fields.Datetime(string='Date de clôture', tracking=True)
    
    priorite = fields.Selection([
        ('1', 'Basse'),
        ('2', 'Normale'),
        ('3', 'Élevée'),
        ('4', 'Critique')
    ], string='Priorité', default='2', tracking=True)
    
    type = fields.Selection([
        ('panne', 'Panne matérielle'),
        ('bug', 'Bug logiciel'),
        ('reseau', 'Problème réseau'),
        ('securite', 'Incident de sécurité'),
        ('demande', 'Demande d\'assistance'),
        ('autre', 'Autre')
    ], string='Type', required=True, tracking=True)
    
    etat = fields.Selection([
        ('nouveau', 'Nouveau'),
        ('en_cours', 'En cours'),
        ('en_attente', 'En attente'),
        ('resolu', 'Résolu'),
        ('annule', 'Annulé')
    ], string='État', default='nouveau', tracking=True)
    
    solution = fields.Text(string='Solution', tracking=True)
    commentaire = fields.Text(string='Commentaires', tracking=True)
    
    client_id = fields.Many2one('it.parc.client', string='Client', required=True, tracking=True)
    materiel_id = fields.Many2one('it.parc.materiel', string='Matériel concerné', tracking=True)
    maintenance_ids = fields.One2many('it.parc.maintenance', 'incident_id', string='Maintenances')
    
    duree = fields.Float(string='Durée (heures)', compute='_compute_duree', store=True)
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string='Nombre d\'interventions')
    
    @api.depends('date_creation', 'date_cloture')
    def _compute_duree(self):
        for incident in self:
            if incident.date_creation and incident.date_cloture:
                delta = incident.date_cloture - incident.date_creation
                incident.duree = delta.total_seconds() / 3600
            else:
                incident.duree = 0
    
    @api.depends('maintenance_ids')
    def _compute_maintenance_count(self):
        for incident in self:
            incident.maintenance_count = len(incident.maintenance_ids)
    
    def action_resoudre(self):
        self.ensure_one()
        self.write({
            'etat': 'resolu',
            'date_cloture': fields.Datetime.now()
        })
    
    def action_annuler(self):
        self.ensure_one()
        self.write({
            'etat': 'annule',
            'date_cloture': fields.Datetime.now()
        })
    
    def action_view_maintenances(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Interventions',
            'view_mode': 'list,form',
            'res_model': 'it.parc.maintenance',
            'domain': [('incident_id', '=', self.id)],
            'context': {
                'default_incident_id': self.id,
                'default_client_id': self.client_id.id,
                'default_materiel_id': self.materiel_id.id,
            },
        }


