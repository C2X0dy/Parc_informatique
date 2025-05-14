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
    
    signature_utilisateur = fields.Binary(string='Signature utilisateur', attachment=True)
    date_signature = fields.Datetime(string='Date de signature')
    conditions_acceptees = fields.Boolean(string='Conditions acceptées')
    
    responsable_id = fields.Many2one('res.users', string='Responsable approbateur')
    etat_approbation = fields.Selection([
        ('a_approuver', 'À approuver'),
        ('approuve', 'Approuvé'),
        ('refuse', 'Refusé')
    ], string='État d\'approbation', default='a_approuver')
    commentaire_approbation = fields.Text(string='Commentaire d\'approbation')

    centre_cout_id = fields.Many2one('account.analytic.account', string='Centre de coût')
    refacturation = fields.Boolean(string='Refacturation interne')
    montant_refacturation = fields.Monetary(string='Montant à refacturer', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)

    motif_retour = fields.Selection([
        ('fin_contrat', 'Fin de contrat'),
        ('depart_utilisateur', 'Départ utilisateur'),
        ('upgrade', 'Remplacement/Upgrade'),
        ('panne', 'Panne/Dysfonctionnement'),
        ('autre', 'Autre')
    ], string='Motif de retour')
    etat_retour = fields.Selection([
        ('bon', 'Bon état'),
        ('acceptable', 'État acceptable'),
        ('deteriore', 'Détérioré'),
        ('defectueux', 'Défectueux')
    ], string='État au retour')
    affectation_suivante_id = fields.Many2one('it.parc.affectation', string='Affectation suivante')
    accessoire_ids = fields.One2many('it.parc.affectation.accessoire', 'affectation_id', string='Accessoires')

    document_conformite_ids = fields.Many2many(
        'ir.attachment', 'affectation_conformite_rel',
        'affectation_id', 'attachment_id',
        string='Documents de conformité'
    )
    charte_signee = fields.Boolean(string='Charte informatique signée')
    reglement_accepte = fields.Boolean(string='Règlement accepté')
    formation_effectuee = fields.Boolean(string='Formation effectuée')

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

    def action_demander_approbation(self):
        self.ensure_one()
        self.etat_approbation = 'a_approuver'
        if self.responsable_id:
            # Envoyer notification
            pass

    def action_approuver(self):
        self.ensure_one()
        self.etat_approbation = 'approuve'
        # Suite du processus d'affectation
        self.action_mettre_en_cours()

    def action_generer_facture_interne(self):
        # Logique de génération de facture interne
        pass

    def action_planifier_retour(self):
        # Planifier le retour du matériel
        pass
    
    def action_retourner(self):
        # Logique de retour avec inspection
        self.ensure_one()
        self.etat = 'terminee'
        self.date_fin = fields.Date.today()
        
        # Mettre à jour l'état du matériel en fonction de l'état retour
        if self.etat_retour in ['bon', 'acceptable']:
            self.materiel_id.etat = 'stock'
        elif self.etat_retour == 'deteriore':
            self.materiel_id.etat = 'maintenance'
        elif self.etat_retour == 'defectueux':
            self.materiel_id.etat = 'panne'


# Nouveau modèle à créer
class AffectationAccessoire(models.Model):
    _name = 'it.parc.affectation.accessoire'
    _description = 'Accessoires inclus dans l\'affectation'
    
    name = fields.Char(string='Description', required=True)
    affectation_id = fields.Many2one('it.parc.affectation', string='Affectation', required=True)
    type = fields.Selection([
        ('souris', 'Souris'),
        ('clavier', 'Clavier'),
        ('ecran', 'Écran'),
        ('dock', 'Station d\'accueil'),
        ('adaptateur', 'Adaptateur/Câble'),
        ('sac', 'Sacoche/Étui'),
        ('autre', 'Autre')
    ], string='Type d\'accessoire', required=True)
    numero_serie = fields.Char(string='Numéro de série')
    etat = fields.Selection([
        ('neuf', 'Neuf'),
        ('bon', 'Bon état'),
        ('use', 'Usé'),
        ('defectueux', 'Défectueux')
    ], string='État', default='bon')
    retourne = fields.Boolean(string='Retourné', default=False)
    commentaire = fields.Text(string='Commentaire')


