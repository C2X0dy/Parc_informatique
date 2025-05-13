from odoo import models, fields, api
from datetime import datetime, timedelta

class TicketIncident(models.Model):
    _name = 'it.parc.ticket'
    _description = 'Ticket d\'incident'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_creation desc'
    
    name = fields.Char(string='Numéro du ticket', required=True, tracking=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('it.parc.ticket'))
    
    objet = fields.Char(string='Objet', tracking=True)

    client_id = fields.Many2one('it.parc.client', string='Client concerné', required=True, tracking=True)
    contact_demandeur = fields.Char(string='Contact demandeur', tracking=True)
    email_demandeur = fields.Char(string='Email demandeur', tracking=True)
    telephone_demandeur = fields.Char(string='Téléphone demandeur', tracking=True)
    
    priorite = fields.Selection([
        ('critique', 'Critique'),
        ('haute', 'Haute'),
        ('moyenne', 'Moyenne'),
        ('faible', 'Faible')
    ], string='Priorité', default='moyenne', tracking=True)
    
    type_incident = fields.Selection([
        ('materiel', 'Matériel'),
        ('logiciel', 'Logiciel'),
        ('reseau', 'Réseau'),
        ('licence', 'Licence'),
        ('autre', 'Autre')
    ], string='Type d\'incident', required=True, tracking=True)
    
    description = fields.Text(string='Description de l\'incident', tracking=True)
    materiel_id = fields.Many2one('it.parc.materiel', string='Matériel concerné', tracking=True,
                                 domain="[('client_id', '=', client_id)]")
    
    date_creation = fields.Datetime(string='Date de signalement', default=fields.Datetime.now, tracking=True)
    date_resolution = fields.Datetime(string='Date de résolution', tracking=True)
    duree_resolution = fields.Float(string='Durée de résolution (heures)', compute='_compute_duree_resolution', store=True)
    
    technicien_id = fields.Many2one('res.users', string='Technicien assigné', tracking=True)
    
    contrat_id = fields.Many2one('it.parc.contrat', string='Contrat SLA applicable', tracking=True,
                                domain="[('client_id', '=', client_id), ('etat', '=', 'actif')]")
    sla_delai_resolution = fields.Integer(string='Délai résolution SLA (heures)', compute='_compute_sla', store=True)
    date_limite_sla = fields.Datetime(string='Date limite résolution SLA', compute='_compute_sla', store=True)
    sla_depasse = fields.Boolean(string='SLA dépassé', compute='_compute_sla_depasse', store=True)
    temps_restant_sla = fields.Float(string='Temps restant SLA (heures)', compute='_compute_temps_restant_sla')
    
    etat = fields.Selection([
        ('nouveau', 'Nouveau'),
        ('en_cours', 'En cours'),
        ('en_attente', 'En attente'),
        ('resolu', 'Résolu'),
        ('clos', 'Clos'),
        ('annule', 'Annulé')
    ], string='État', default='nouveau', tracking=True)
    
    rapport_intervention = fields.Text(string='Rapport d\'intervention', tracking=True)
    solution = fields.Text(string='Solution apportée', tracking=True)
    
    # Pièces jointes
    captures_ecran_ids = fields.Many2many(
        'ir.attachment', 'ticket_captures_rel',
        'ticket_id', 'attachment_id',
        string='Captures d\'écran'
    )
    logs_ids = fields.Many2many(
        'ir.attachment', 'ticket_logs_rel',
        'ticket_id', 'attachment_id',
        string='Logs techniques'
    )
    
    # Relations
    incident_id = fields.Many2one('it.parc.incident', string='Incident lié')
    maintenance_ids = fields.One2many('it.parc.maintenance', 'ticket_id', string='Interventions')
    historique_ids = fields.One2many('it.parc.ticket.historique', 'ticket_id', string='Historique des actions')
    
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string='Nombre d\'interventions')
    
    @api.depends('maintenance_ids')
    def _compute_maintenance_count(self):
        for ticket in self:
            ticket.maintenance_count = len(ticket.maintenance_ids)
    
    @api.depends('date_creation', 'date_resolution')
    def _compute_duree_resolution(self):
        for ticket in self:
            if ticket.date_creation and ticket.date_resolution:
                delta = ticket.date_resolution - ticket.date_creation
                ticket.duree_resolution = delta.total_seconds() / 3600
            else:
                ticket.duree_resolution = 0
    
    @api.depends('contrat_id')
    def _compute_sla(self):
        for ticket in self:
            if ticket.contrat_id and ticket.contrat_id.sla_delai_resolution:
                ticket.sla_delai_resolution = ticket.contrat_id.sla_delai_resolution
                if ticket.date_creation:
                    heures = ticket.sla_delai_resolution
                    date_limite = ticket.date_creation + timedelta(hours=heures)
                    ticket.date_limite_sla = date_limite
                else:
                    ticket.date_limite_sla = False
            else:
                # SLA par défaut si aucun contrat n'est spécifié
                ticket.sla_delai_resolution = 0
                ticket.date_limite_sla = False
    
    @api.depends('date_limite_sla', 'etat')
    def _compute_sla_depasse(self):
        maintenant = fields.Datetime.now()
        for ticket in self:
            # SLA dépassé si date limite atteinte et ticket pas encore résolu
            if ticket.date_limite_sla and ticket.etat in ['nouveau', 'en_cours', 'en_attente']:
                ticket.sla_depasse = maintenant > ticket.date_limite_sla
            else:
                ticket.sla_depasse = False
    
    @api.depends('date_limite_sla', 'etat')
    def _compute_temps_restant_sla(self):
        maintenant = fields.Datetime.now()
        for ticket in self:
            # Calcul temps restant uniquement si date limite définie et ticket en cours
            if ticket.date_limite_sla and ticket.etat in ['nouveau', 'en_cours', 'en_attente']:
                if maintenant < ticket.date_limite_sla:
                    delta = ticket.date_limite_sla - maintenant
                    ticket.temps_restant_sla = delta.total_seconds() / 3600
                else:
                    ticket.temps_restant_sla = 0
            else:
                ticket.temps_restant_sla = 0
    
    def action_en_cours(self):
        self.ensure_one()
        self.etat = 'en_cours'
        self._create_action_history('en_cours', 'Ticket pris en charge')
        
        # Si technicien non assigné, assigner l'utilisateur courant
        if not self.technicien_id:
            self.technicien_id = self.env.user.id
    
    def action_en_attente(self):
        self.ensure_one()
        self.etat = 'en_attente'
        self._create_action_history('en_attente', 'Ticket mis en attente')
    
    def action_resoudre(self):
        self.ensure_one()
        self.write({
            'etat': 'resolu',
            'date_resolution': fields.Datetime.now()
        })
        self._create_action_history('resolu', 'Ticket résolu')
    
    def action_clore(self):
        self.ensure_one()
        self.etat = 'clos'
        self._create_action_history('clos', 'Ticket clôturé')
    
    def action_annuler(self):
        self.ensure_one()
        self.etat = 'annule'
        self._create_action_history('annule', 'Ticket annulé')
    
    def action_creer_intervention(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créer une intervention',
            'view_mode': 'form',
            'res_model': 'it.parc.maintenance',
            'context': {
                'default_ticket_id': self.id,
                'default_client_id': self.client_id.id,
                'default_materiel_id': self.materiel_id.id if self.materiel_id else False,
                'default_description': f"Intervention liée au ticket {self.name}\n\n{self.description or ''}",
                'default_type': 'corrective',
            },
            'target': 'new',
        }
    
    def action_view_maintenances(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Interventions',
            'view_mode': 'list,form',
            'res_model': 'it.parc.maintenance',
            'domain': [('ticket_id', '=', self.id)],
            'context': {
                'default_ticket_id': self.id,
                'default_client_id': self.client_id.id,
                'default_materiel_id': self.materiel_id.id if self.materiel_id else False,
            },
        }
    
    def action_convert_to_incident(self):
        """Convertir un ticket en incident formel"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créer un incident',
            'view_mode': 'form',
            'res_model': 'it.parc.incident',
            'context': {
                'default_client_id': self.client_id.id,
                'default_materiel_id': self.materiel_id.id if self.materiel_id else False,
                'default_description': f"Incident créé depuis le ticket {self.name}\n\n{self.description or ''}",
                'default_objet': f"[{self.name}] {self.type_incident}",
                'default_type': 'panne' if self.type_incident == 'materiel' else (
                    'bug' if self.type_incident == 'logiciel' else (
                    'reseau' if self.type_incident == 'reseau' else 'autre')),
                'default_priorite': '4' if self.priorite == 'critique' else (
                    '3' if self.priorite == 'haute' else (
                    '2' if self.priorite == 'moyenne' else '1')),
            },
            'target': 'new',
        }
    
    def _create_action_history(self, action_type, description=''):
        """Créer une entrée dans l'historique du ticket"""
        self.env['it.parc.ticket.historique'].create({
            'ticket_id': self.id,
            'utilisateur_id': self.env.user.id,
            'date': fields.Datetime.now(),
            'action': action_type,
            'description': description
        })
    
    @api.model
    def create(self, vals):
        result = super(TicketIncident, self).create(vals)
        # Créer une entrée dans l'historique lors de la création
        result._create_action_history('creation', 'Ticket créé')
        return result
    
    def write(self, vals):
        # Traçabilité des changements importants
        if 'technicien_id' in vals and self.technicien_id.id != vals['technicien_id']:
            nouveau_technicien = self.env['res.users'].browse(vals['technicien_id']).name
            self._create_action_history('assignation', f'Ticket assigné à {nouveau_technicien}')
            
        return super(TicketIncident, self).write(vals)


class TicketHistorique(models.Model):
    _name = 'it.parc.ticket.historique'
    _description = 'Historique des actions sur ticket'
    _order = 'date desc'
    
    ticket_id = fields.Many2one('it.parc.ticket', string='Ticket', required=True, ondelete='cascade')
    utilisateur_id = fields.Many2one('res.users', string='Utilisateur', required=True)
    date = fields.Datetime(string='Date', required=True)
    
    action = fields.Selection([
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('en_cours', 'Prise en charge'),
        ('en_attente', 'Mise en attente'),
        ('resolu', 'Résolution'),
        ('clos', 'Clôture'),
        ('annule', 'Annulation'),
        ('assignation', 'Assignation'),
        ('intervention', 'Intervention'),
        ('commentaire', 'Commentaire'),
    ], string='Action', required=True)
    
    description = fields.Text(string='Description')