from odoo import models, fields, api


class Affectation(models.Model):
    _name = 'it.parc.affectation'
    _description = 'Affectation de matériel'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Référence', required=True, tracking=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('it.parc.affectation'))
    
    date_debut = fields.Date(string='Date de début', required=True, default=fields.Date.today, tracking=True)
    date_fin = fields.Date(string='Date de fin', tracking=True)
    
    etat = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée')
    ], string='État', default='brouillon', tracking=True)
    
    materiel_id = fields.Many2one('it.parc.materiel', string='Matériel', required=True, tracking=True)
    utilisateur_nom = fields.Char(string='Nom de l\'utilisateur', required=True, tracking=True)
    utilisateur_email = fields.Char(string='Email de l\'utilisateur', tracking=True)
    departement = fields.Char(string='Département', tracking=True)
    
    commentaire = fields.Text(string='Commentaires', tracking=True)
    
    def action_mettre_en_cours(self):
        self.ensure_one()
        self.etat = 'en_cours'
        # Mettre à jour l'état du matériel
        if self.materiel_id:
            self.materiel_id.etat = 'actif'
    
    def action_terminer(self):
        self.ensure_one()
        self.write({
            'etat': 'terminee',
            'date_fin': fields.Date.today()
        })
        # Remettre le matériel en stock
        if self.materiel_id:
            self.materiel_id.etat = 'stock'
    
    def action_annuler(self):
        self.ensure_one()
        self.etat = 'annulee'


