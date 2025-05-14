from odoo import models, fields, api, tools
from datetime import timedelta
import json

class ITDashboard(models.Model):
    _name = 'it.parc.dashboard'
    _description = 'Tableau de bord du parc IT'
    _auto = False

    name = fields.Char(string='Nom', default='Dashboard')
    
    # Compteurs
    total_clients = fields.Integer(string='Total clients', compute='_compute_stats')
    total_materiels = fields.Integer(string='Total matériels', compute='_compute_stats')
    total_contrats = fields.Integer(string='Total contrats', compute='_compute_stats')
    incidents_en_cours = fields.Integer(string='Incidents en cours', compute='_compute_stats')
    total_maintenances = fields.Integer(string='Total interventions', compute='_compute_stats')
    factures_non_payees = fields.Integer(string='Factures en attente', compute='_compute_stats')
    garanties_expirees = fields.Integer(string='Garanties expirées', compute='_compute_stats')
    affectations_actives = fields.Integer(string='Affectations actives', compute='_compute_stats')
    
    # Données pour graphiques
    incident_type_chart = fields.Char(string='Incidents par type', compute='_compute_stats')
    materiel_client_chart = fields.Char(string='Matériels par client', compute='_compute_stats')
    maintenance_etat_chart = fields.Char(string='Interventions par état', compute='_compute_stats')
    ticket_resolution_time_chart = fields.Char(string='Temps de résolution', compute='_compute_stats')
    top_clients_ca_chart = fields.Char(string='Top clients par CA', compute='_compute_stats')
    contrats_par_mois_chart = fields.Char(string='Contrats par mois', compute='_compute_stats')

    # Statistiques tickets
    tickets_en_cours = fields.Integer(string='Tickets en cours', compute='_compute_stats')
    tickets_sla_depasse = fields.Integer(string='Tickets SLA dépassé', compute='_compute_stats')

    # Statistiques abonnements
    abonnements_actifs = fields.Integer(string='Abonnements actifs', compute='_compute_stats')
    facturations_a_venir = fields.Integer(string='Facturations à venir', compute='_compute_stats')

    # Ajoutez ce champ pour afficher la liste des tickets SLA dépassés
    tickets_sla_depasses_ids = fields.Many2many('it.parc.ticket', string='Tickets SLA dépassés', compute='_compute_tickets_sla')

    def init(self):
        # Fix: Create the table properly for _auto=False model
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 1 as id,
                       'Dashboard' as name
            )
        """ % self._table)
    
    @api.depends_context('uid')
    def _compute_stats(self):
        for record in self:
            # Calcul des compteurs
            record.total_clients = self.env['it.parc.client'].search_count([])
            record.total_materiels = self.env['it.parc.materiel'].search_count([])
            record.total_contrats = self.env['it.parc.contrat'].search_count([])
            record.incidents_en_cours = self.env['it.parc.incident'].search_count([
                ('etat', 'in', ['nouveau', 'en_cours', 'en_attente'])
            ])
            record.total_maintenances = self.env['it.parc.maintenance'].search_count([])
            record.factures_non_payees = self.env['it.parc.facturation'].search_count([
                ('etat', 'in', ['brouillon', 'envoyee'])
            ])
            record.garanties_expirees = self.env['it.parc.materiel'].search_count([
                ('garantie_valide', '=', False),
                ('date_fin_garantie', '!=', False)
            ])
            record.affectations_actives = self.env['it.parc.affectation'].search_count([
                ('etat', '=', 'en_cours')
            ])
            
            # Préparation des données pour les graphiques
            # Ces données seront utilisées par les widgets de graphique
            record.incident_type_chart = 'data'
            record.materiel_client_chart = 'data'
            record.maintenance_etat_chart = 'data'

            # Statistiques tickets
            record.tickets_en_cours = self.env['it.parc.ticket'].search_count([
                ('etat', 'in', ['nouveau', 'en_cours', 'en_attente'])
            ])
            record.tickets_sla_depasse = self.env['it.parc.ticket'].search_count([
                ('sla_depasse', '=', True),
                ('etat', 'in', ['nouveau', 'en_cours', 'en_attente'])
            ])
            record.abonnements_actifs = self.env['it.parc.abonnement'].search_count([
                ('etat', '=', 'actif')
            ])
            record.facturations_a_venir = self.env['it.parc.abonnement'].search_count([
                ('etat', '=', 'actif'),
                ('prochaine_facturation', '!=', False),
                ('prochaine_facturation', '<=', fields.Date.today() + timedelta(days=7))
            ])
            
            # Ajoutez ces calculs pour les nouveaux graphiques
            # Temps moyen de résolution des tickets
            tickets_resolus = self.env['it.parc.ticket'].search([
                ('etat', '=', 'resolu'),
                ('date_resolution', '!=', False),
                ('date_creation', '!=', False)
            ])
            temps_resolution_data = []
            for ticket in tickets_resolus:
                duree = (ticket.date_resolution - ticket.date_creation).total_seconds() / 3600
                temps_resolution_data.append({
                    'x': ticket.date_resolution.strftime('%Y-%m-%d'),
                    'y': duree,
                    'label': ticket.name
                })
            record.ticket_resolution_time_chart = json.dumps(temps_resolution_data)
            
            # Top clients par CA
            clients = self.env['it.parc.client'].search([], limit=10)
            top_clients_data = []
            for client in clients:
                ca = sum(facture.montant_ttc for facture in self.env['it.parc.facturation'].search([
                    ('client_id', '=', client.id),
                    ('etat', '=', 'payee')
                ]))
                if ca > 0:
                    top_clients_data.append({
                        'x': client.name,
                        'y': ca
                    })
            record.top_clients_ca_chart = json.dumps(sorted(top_clients_data, key=lambda x: x['y'], reverse=True))

    @api.depends_context('uid')
    def _compute_tickets_sla(self):
        for record in self:
            record.tickets_sla_depasses_ids = self.env['it.parc.ticket'].search([
                ('sla_depasse', '=', True),
                ('etat', 'in', ['nouveau', 'en_cours', 'en_attente'])
            ], order='date_limite_sla asc')


