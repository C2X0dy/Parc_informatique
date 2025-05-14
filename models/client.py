from odoo import models, fields, api


class Client(models.Model):
    _name = 'it.parc.client'
    _description = 'Client du parc informatique'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Raison sociale', required=True, tracking=True)
    code = fields.Char(string='Code client', tracking=True)
    type_client = fields.Selection([
        ('pme', 'PME'),
        ('collectivite', 'Collectivité'),
        ('grand_compte', 'Grand compte'),
        ('autre', 'Autre')
    ], string='Type de client', default='pme', tracking=True)
    siret = fields.Char(string='Numéro SIRET', tracking=True)
    address = fields.Text(string='Adresse principale', tracking=True)
    address_secondary = fields.Text(string='Adresse secondaire', tracking=True)
    
    # Contact principal
    contact_name = fields.Char(string='Nom du contact principal', tracking=True)
    phone = fields.Char(string='Téléphone', tracking=True)
    mobile = fields.Char(string='Mobile', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    
    portal_url = fields.Char(string='Lien portail client', tracking=True)
    total_postes = fields.Integer(string='Nombre de postes gérés', tracking=True, 
                                 compute='_compute_total_postes', store=True)
    
    active = fields.Boolean(default=True, tracking=True)
    
    # Relations existantes
    contrat_ids = fields.One2many('it.parc.contrat', 'client_id', string='Contrats')
    materiel_ids = fields.One2many('it.parc.materiel', 'client_id', string='Matériels')
    incident_ids = fields.One2many('it.parc.incident', 'client_id', string='Incidents')
    site_ids = fields.One2many('it.parc.site', 'client_id', string='Sites')
    
    # Compteurs existants
    contrat_count = fields.Integer(compute='_compute_contrat_count', string='Nombre de contrats')
    materiel_count = fields.Integer(compute='_compute_materiel_count', string='Nombre de matériels')
    incident_count = fields.Integer(compute='_compute_incident_count', string='Nombre d\'incidents')
    site_count = fields.Integer(compute='_compute_site_count', string='Nombre de sites')
    
    # Add this field to link clients to portal users
    partner_id = fields.Many2one('res.partner', string='Contact associé', help="Lien vers le partenaire Odoo pour l'accès au portail")
    
    @api.depends('materiel_ids')
    def _compute_total_postes(self):
        for client in self:
            # Compter uniquement les matériels de type 'ordinateur' ou 'mobile'
            client.total_postes = self.env['it.parc.materiel'].search_count([
                ('client_id', '=', client.id),
                ('type', 'in', ['ordinateur', 'mobile']),
                ('etat', 'in', ['actif', 'maintenance', 'panne'])
            ])
    
    @api.depends('contrat_ids')
    def _compute_contrat_count(self):
        for client in self:
            client.contrat_count = len(client.contrat_ids)
            
    @api.depends('materiel_ids')
    def _compute_materiel_count(self):
        for client in self:
            client.materiel_count = len(client.materiel_ids)
            
    @api.depends('incident_ids')
    def _compute_incident_count(self):
        for client in self:
            client.incident_count = len(client.incident_ids)
            
    @api.depends('site_ids')
    def _compute_site_count(self):
        for client in self:
            client.site_count = len(client.site_ids)
            
    def action_view_contrats(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrats',
            'view_mode': 'list,form',
            'res_model': 'it.parc.contrat',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id},
        }
    
    def action_view_materiels(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Matériels',
            'view_mode': 'list,form',
            'res_model': 'it.parc.materiel',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id},
        }
    
    def action_view_incidents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Incidents',
            'view_mode': 'list,form',
            'res_model': 'it.parc.incident',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id},
        }
    
    def action_view_sites(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sites',
            'view_mode': 'list,form',
            'res_model': 'it.parc.site',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id},
        }


