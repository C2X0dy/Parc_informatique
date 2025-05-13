from odoo import models, fields, api

class Facturation(models.Model):
    _name = 'it.parc.facturation'
    _description = 'Facturation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    
    name = fields.Char(string='Numéro de facture', required=True, tracking=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('it.parc.facturation'))
    date = fields.Date(string='Date de facturation', required=True, default=fields.Date.today, tracking=True)
    echeance = fields.Date(string='Date d\'échéance', tracking=True)
    
    montant_ht = fields.Float(string='Montant HT', required=True, tracking=True)
    taux_tva = fields.Float(string='Taux TVA (%)', default=20.0, tracking=True)
    montant_tva = fields.Float(string='Montant TVA', compute='_compute_montants', store=True)
    montant_ttc = fields.Float(string='Montant TTC', compute='_compute_montants', store=True)
    
    devise = fields.Selection([
        ('eur', 'EUR (€)'),
        ('usd', 'USD ($)'),
        ('mad', 'MAD (DH)'),
    ], string='Devise', default='eur', tracking=True)
    
    etat = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('envoyee', 'Envoyée'),
        ('payee', 'Payée'),
        ('annulee', 'Annulée')
    ], string='État', default='brouillon', tracking=True)
    
    description = fields.Text(string='Description', tracking=True)
    notes = fields.Text(string='Notes', tracking=True)
    
    client_id = fields.Many2one('it.parc.client', string='Client', required=True, tracking=True)
    contrat_id = fields.Many2one('it.parc.contrat', string='Contrat associé', tracking=True)
    abonnement_id = fields.Many2one('it.parc.abonnement', string='Abonnement source', tracking=True)
    mode_paiement = fields.Selection([
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('cb', 'Carte bancaire'),
        ('especes', 'Espèces'),
        ('prelevement', 'Prélèvement')
    ], string='Mode de paiement', tracking=True)
    maintenance_ids = fields.Many2many('it.parc.maintenance', string='Interventions associées')
    
    @api.depends('montant_ht', 'taux_tva')
    def _compute_montants(self):
        for facture in self:
            facture.montant_tva = facture.montant_ht * (facture.taux_tva / 100.0)
            facture.montant_ttc = facture.montant_ht + facture.montant_tva
    
    def action_envoyer(self):
        self.ensure_one()
        self.etat = 'envoyee'
    
    def action_marquer_payee(self):
        self.ensure_one()
        self.etat = 'payee'
    
    def action_annuler(self):
        self.ensure_one()
        self.etat = 'annulee'
    
    def action_reinitialiser(self):
        self.ensure_one()
        self.etat = 'brouillon'
    
    def action_view_maintenances(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Interventions',
            'view_mode': 'list,form',
            'res_model': 'it.parc.maintenance',
            'domain': [('id', 'in', self.maintenance_ids.ids)],
            'context': {'default_client_id': self.client_id.id, 'default_facturable': True},
        }


