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
    
    # Add this field to link clients to portal users
    partner_id = fields.Many2one('res.partner', string='Contact associé', help="Lien vers le partenaire Odoo pour l'accès au portail")
    
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
    
    # Nouveaux champs pour la personnalisation
    logo = fields.Binary(string='Logo de l\'entreprise', attachment=True, 
                         help="Logo qui sera affiché sur le portail client")
    couleur_primaire = fields.Char(string='Couleur primaire', 
                                  default="#3c4ea0", 
                                  help="Code couleur hexadécimal (ex: #3c4ea0)")
    couleur_secondaire = fields.Char(string='Couleur secondaire', 
                                    default="#28a745",
                                    help="Code couleur hexadécimal (ex: #28a745)")
    slogan = fields.Char(string='Slogan', 
                         help="Un court slogan qui sera affiché sur le portail")
    presentation = fields.Html(string='Présentation', 
                            help="Brève présentation de l'entreprise")
    secteur_activite = fields.Selection([
        ('informatique', 'Informatique & Technologie'),
        ('sante', 'Santé & Médical'),
        ('education', 'Éducation & Formation'),
        ('finance', 'Finance & Assurance'),
        ('commerce', 'Commerce & Distribution'),
        ('industrie', 'Industrie & Manufacture'),
        ('service', 'Services aux entreprises'),
        ('public', 'Secteur public'),
        ('associations', 'Associations & ONG'),
        ('autre', 'Autre')
    ], string='Secteur d\'activité', default='autre', tracking=True)
    taille_entreprise = fields.Selection([
        ('tpe', 'TPE (< 10 employés)'),
        ('pme', 'PME (10-250 employés)'),
        ('eti', 'ETI (250-5000 employés)'),
        ('ge', 'Grande entreprise (> 5000 employés)')
    ], string='Taille de l\'entreprise', default='pme', tracking=True)
    date_creation = fields.Date(string='Date de création de l\'entreprise')
    site_web = fields.Char(string='Site web')
    reseaux_sociaux = fields.One2many('it.parc.client.social', 'client_id', string='Réseaux sociaux')
    
    # Préférences de tableaux de bord
    widget_incident_stats = fields.Boolean(string='Widget stats incidents', default=True)
    widget_equipment_stats = fields.Boolean(string='Widget stats équipements', default=True)
    widget_budget_forecast = fields.Boolean(string='Widget prévisions budgétaires', default=True)
    widget_contracts = fields.Boolean(string='Widget contrats', default=True)
    widget_upcoming_events = fields.Boolean(string='Widget événements à venir', default=True)
    widget_performance = fields.Boolean(string='Widget performance', default=True)

    # Préférences de notification
    notify_ticket_created_email = fields.Boolean(string='Email - Création ticket', default=True)
    notify_ticket_created_sms = fields.Boolean(string='SMS - Création ticket', default=False)
    notify_ticket_updated_email = fields.Boolean(string='Email - Mise à jour ticket', default=True)
    notify_ticket_updated_sms = fields.Boolean(string='SMS - Mise à jour ticket', default=False)
    notify_contract_expiry_email = fields.Boolean(string='Email - Expiration contrat', default=True)
    notify_contract_expiry_sms = fields.Boolean(string='SMS - Expiration contrat', default=False)
    notify_maintenance_email = fields.Boolean(string='Email - Maintenance', default=True)
    notify_maintenance_sms = fields.Boolean(string='SMS - Maintenance', default=False)
    notify_invoice_email = fields.Boolean(string='Email - Facturation', default=True)
    notify_invoice_sms = fields.Boolean(string='SMS - Facturation', default=False)

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


class ClientReseauxSociaux(models.Model):
    _name = 'it.parc.client.social'
    _description = 'Réseaux sociaux du client'
    
    client_id = fields.Many2one('it.parc.client', string='Client', required=True, ondelete='cascade')
    type = fields.Selection([
        ('linkedin', 'LinkedIn'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter/X'),
        ('instagram', 'Instagram'),
        ('youtube', 'YouTube'),
        ('autre', 'Autre')
    ], string='Type', required=True)
    nom = fields.Char(string='Nom du compte')
    url = fields.Char(string='URL', required=True)



