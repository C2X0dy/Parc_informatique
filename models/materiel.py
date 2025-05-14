from odoo import models, fields, api, _
from datetime import date
from dateutil.relativedelta import relativedelta
import logging
from odoo.exceptions import UserError
import uuid
from urllib.parse import quote

_logger = logging.getLogger(__name__)

class MaterielCategorie(models.Model):
    _name = 'it.parc.materiel.categorie'
    _description = 'Catégorie de matériel'
    _order = 'name'

    name = fields.Char('Nom', required=True)
    code = fields.Char('Code')
    description = fields.Text('Description')
    parent_id = fields.Many2one('it.parc.materiel.categorie', string='Catégorie parente')
    child_ids = fields.One2many('it.parc.materiel.categorie', 'parent_id', string='Sous-catégories')
    
class Materiel(models.Model):
    _name = 'it.parc.materiel'
    _description = 'Matériel informatique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Nom', required=True, tracking=True)
    
    # Informations d'identification
    num_inventaire = fields.Char(string='Numéro d\'inventaire', tracking=True)
    reference = fields.Char(string='Référence', tracking=True)
    marque = fields.Char(string='Marque', tracking=True)
    modele = fields.Char(string='Modèle', tracking=True)
    serial_number = fields.Char(string='Numéro de série', tracking=True)
    
    # Classification
    categorie_id = fields.Many2one('it.parc.materiel.categorie', string='Catégorie', tracking=True)
    type = fields.Selection([
        ('ordinateur', 'Ordinateur'),
        ('serveur', 'Serveur'),
        ('imprimante', 'Imprimante'),
        ('reseau', 'Équipement réseau'),
        ('stockage', 'Stockage'),
        ('mobile', 'Mobile/Tablette'),
        ('peripherique', 'Périphérique'),
        ('autre', 'Autre')
    ], string='Type', required=True, tracking=True)
    
    type_utilisation = fields.Selection([
        ('fixe', 'Poste fixe'),
        ('serveur', 'Serveur'),
        ('mobile', 'Mobile'),
        ('reseau', 'Périphérique réseau'),
        ('peripherique', 'Périphérique'),
        ('autre', 'Autre')
    ], string='Type d\'utilisation', tracking=True)
    
    # Dates importantes
    date_acquisition = fields.Date(string='Date d\'achat', tracking=True)
    date_mise_service = fields.Date(string='Date de mise en service', tracking=True)
    date_fin_garantie = fields.Date(string='Date de fin de garantie', tracking=True)
    
    # État et localisation
    etat = fields.Selection([
        ('stock', 'En stock'),
        ('actif', 'En service'),
        ('maintenance', 'En maintenance'),
        ('panne', 'En panne'),
        ('obsolete', 'Obsolète'),
        ('rebut', 'Mis au rebut'),
        ('hs', 'Hors service')
    ], string='État', default='stock', tracking=True)
    
    site_id = fields.Many2one('it.parc.site', string='Site', tracking=True)
    emplacement = fields.Char(string='Emplacement', tracking=True)
    
    # Affectation
    client_id = fields.Many2one('it.parc.client', string='Client', tracking=True)
    contrat_id = fields.Many2one('it.parc.contrat', string='Contrat de maintenance', tracking=True)
    service_affectation = fields.Char(string='Service d\'affectation', tracking=True)
    utilisateur_affectation = fields.Char(string='Utilisateur affecté', tracking=True)
    
    # Informations financières améliorées
    prix_achat_ht = fields.Float(string='Prix d\'achat HT', tracking=True)
    valeur_residuelle = fields.Float(string='Valeur résiduelle', tracking=True)
    devise = fields.Selection([
        ('eur', 'EUR (€)'),
        ('usd', 'USD ($)'),
        ('mad', 'MAD (DH)'),
        ('cfa', 'CFA (FCFA)'),
    ], string='Devise', default='eur', tracking=True)
    fournisseur_id = fields.Many2one('res.partner', string='Fournisseur', tracking=True)
    # Si vous préférez utiliser un champ texte simple, utilisez un nom différent pour éviter les conflits :
    nom_fournisseur = fields.Char(string='Nom du fournisseur', tracking=True)
    
    # Nouveaux champs pour l'amortissement
    amortissement_active = fields.Boolean(string='Activer l\'amortissement', default=False, tracking=True)
    duree_amortissement = fields.Integer(string='Durée d\'amortissement (mois)', default=36, tracking=True)
    methode_amortissement = fields.Selection([
        ('lineaire', 'Linéaire'),
        ('degressif', 'Dégressif')
    ], string='Méthode d\'amortissement', default='lineaire', tracking=True)
    taux_degressif = fields.Float(string='Taux dégressif', default=1.75, 
        help="Coefficient multiplicateur pour l'amortissement dégressif (généralement 1.25, 1.75, 2.25)")
    date_debut_amortissement = fields.Date(string='Date de début d\'amortissement', 
        default=lambda self: self.date_mise_service or fields.Date.today(), tracking=True)
    valeur_comptable = fields.Float(string='Valeur nette comptable', compute='_compute_valeur_comptable', store=True)
    amortissement_ids = fields.One2many('it.parc.materiel.amortissement', 'materiel_id', 
        string='Lignes d\'amortissement')
    
    # Description et notes
    description = fields.Text(string='Description', tracking=True)
    remarques = fields.Text(string='Remarques internes', tracking=True)
    specifications = fields.Text(string='Spécifications techniques', tracking=True)
    
    # Configuration réseau
    ip_address = fields.Char(string='Adresse IP', tracking=True)
    mac_address = fields.Char(string='Adresse MAC', tracking=True)
    hostname = fields.Char(string='Nom d\'hôte', tracking=True)
    
    # Relations
    incident_ids = fields.One2many('it.parc.incident', 'materiel_id', string='Incidents')
    affectation_ids = fields.One2many('it.parc.affectation', 'materiel_id', string='Affectations')
    
    # Pièces jointes spécifiques
    facture_attachment_ids = fields.Many2many(
        'ir.attachment', 'materiel_facture_attachment_rel',
        'materiel_id', 'attachment_id',
        string='Factures d\'achat'
    )
    garantie_attachment_ids = fields.Many2many(
        'ir.attachment', 'materiel_garantie_attachment_rel',
        'materiel_id', 'attachment_id',
        string='Documents de garantie'
    )
    fiche_technique_attachment_ids = fields.Many2many(
        'ir.attachment', 'materiel_fiche_attachment_rel',
        'materiel_id', 'attachment_id',
        string='Fiches techniques'
    )
    
    # Champs calculés
    incident_count = fields.Integer(compute='_compute_incident_count', string='Nombre d\'incidents')
    garantie_valide = fields.Boolean(compute='_compute_garantie_valide', string='Garantie valide', store=True)
    jours_restant_garantie = fields.Integer(compute='_compute_garantie_valide', string='Jours restants garantie', store=True)
    duree_utilisation = fields.Integer(compute='_compute_duree_utilisation', string='Durée d\'utilisation (jours)', store=True)
    qr_code_url = fields.Char(string='URL QR Code', compute='_compute_qr_code_url', store=True)
    access_token = fields.Char(string='Token d\'accès', copy=False, default=lambda self: str(uuid.uuid4()))

    @api.depends('incident_ids')
    def _compute_incident_count(self):
        for materiel in self:
            materiel.incident_count = len(materiel.incident_ids)
    
    @api.depends('date_fin_garantie')
    def _compute_garantie_valide(self):
        today = date.today()
        for materiel in self:
            if materiel.date_fin_garantie:
                delta = (materiel.date_fin_garantie - today).days
                materiel.jours_restant_garantie = delta
                materiel.garantie_valide = delta >= 0
            else:
                materiel.jours_restant_garantie = 0
                materiel.garantie_valide = False
    
    @api.depends('date_mise_service')
    def _compute_duree_utilisation(self):
        today = date.today()
        for materiel in self:
            if materiel.date_mise_service:
                materiel.duree_utilisation = (today - materiel.date_mise_service).days
            else:
                materiel.duree_utilisation = 0
            
    @api.depends('prix_achat_ht', 'amortissement_ids', 'amortissement_active')
    def _compute_valeur_comptable(self):
        for materiel in self:
            if not materiel.amortissement_active or not materiel.prix_achat_ht:
                materiel.valeur_comptable = materiel.prix_achat_ht
                continue
                
            # Somme des amortissements comptabilisés
            amortissement_total = sum(ligne.montant for ligne in materiel.amortissement_ids if ligne.state == 'comptabilise')
            materiel.valeur_comptable = materiel.prix_achat_ht - amortissement_total
    
    @api.depends('access_token')
    def _compute_qr_code_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for materiel in self:
            if materiel.access_token:
                materiel.qr_code_url = f"{base_url}/materiel/info/{materiel.id}/{materiel.access_token}"
            else:
                materiel.qr_code_url = False
    
    @api.onchange('date_mise_service')
    def _onchange_date_mise_service(self):
        if self.date_mise_service and not self.date_debut_amortissement:
            self.date_debut_amortissement = self.date_mise_service
    
    def action_view_incidents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Incidents',
            'view_mode': 'list,form',
            'res_model': 'it.parc.incident',
            'domain': [('materiel_id', '=', self.id)],
            'context': {'default_materiel_id': self.id, 'default_client_id': self.client_id.id},
        }

    def action_view_affectations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Affectations',
            'view_mode': 'list,form',
            'res_model': 'it.parc.affectation',
            'domain': [('materiel_id', '=', self.id)],
            'context': {'default_materiel_id': self.id},
        }
        
    def action_passer_en_maintenance(self):
        self.ensure_one()
        self.etat = 'maintenance'
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créer une intervention',
            'view_mode': 'form',
            'res_model': 'it.parc.maintenance',
            'context': {
                'default_materiel_id': self.id,
                'default_client_id': self.client_id.id,
                'default_type': 'corrective',
            },
            'target': 'new',
        }
        
    def action_marquer_obsolete(self):
        self.ensure_one()
        self.etat = 'obsolete'
        
    def action_marquer_rebut(self):
        self.ensure_one()
        self.etat = 'rebut'
        
    def action_remettre_en_service(self):
        self.ensure_one()
        self.etat = 'actif'
    
    def action_calculer_amortissement(self):
        """Calcule le tableau d'amortissement pour le matériel"""
        self.ensure_one()
        
        if not self.amortissement_active or not self.prix_achat_ht or not self.date_debut_amortissement:
            raise UserError(_("Veuillez activer l'amortissement et renseigner le prix d'achat et la date de début d'amortissement."))
        
        # Effacer les anciennes lignes non comptabilisées
        self.amortissement_ids.filtered(lambda r: r.state != 'comptabilise').unlink()
        
        # Valeur amortissable
        valeur_amortissable = self.prix_achat_ht - self.valeur_residuelle
        
        # Calcul du tableau d'amortissement
        if self.methode_amortissement == 'lineaire':
            # Amortissement linéaire
            montant_mensuel = valeur_amortissable / self.duree_amortissement
            valeur_restante = valeur_amortissable
            
            for i in range(1, self.duree_amortissement + 1):
                date_debut = self.date_debut_amortissement + relativedelta(months=i-1)
                date_fin = self.date_debut_amortissement + relativedelta(months=i) - relativedelta(days=1)
                
                # Dernier mois: ajuster pour éviter les erreurs d'arrondi
                if i == self.duree_amortissement:
                    montant = valeur_restante
                else:
                    montant = montant_mensuel
                
                valeur_restante -= montant
                
                self.env['it.parc.materiel.amortissement'].create({
                    'materiel_id': self.id,
                    'sequence': i,
                    'date_debut': date_debut,
                    'date_fin': date_fin,
                    'montant': montant,
                    'cumul': self.prix_achat_ht - valeur_restante - self.valeur_residuelle,
                    'valeur_residuelle': valeur_restante + self.valeur_residuelle,
                    'state': 'brouillon'
                })
        else:
            # Amortissement dégressif
            taux_lineaire = 1 / self.duree_amortissement
            taux_degressif = taux_lineaire * self.taux_degressif
            valeur_restante = valeur_amortissable
            
            for i in range(1, self.duree_amortissement + 1):
                date_debut = self.date_debut_amortissement + relativedelta(months=i-1)
                date_fin = self.date_debut_amortissement + relativedelta(months=i) - relativedelta(days=1)
                
                # Basculement en linéaire si plus avantageux
                taux_restant = 1 / (self.duree_amortissement - i + 1)
                if taux_restant > taux_degressif:
                    montant = valeur_restante * taux_restant
                else:
                    montant = valeur_restante * taux_degressif
                
                # Dernier mois: ajuster pour éviter les erreurs d'arrondi
                if i == self.duree_amortissement:
                    montant = valeur_restante
                
                valeur_restante -= montant
                
                self.env['it.parc.materiel.amortissement'].create({
                    'materiel_id': self.id,
                    'sequence': i,
                    'date_debut': date_debut,
                    'date_fin': date_fin,
                    'montant': montant,
                    'cumul': self.prix_achat_ht - valeur_restante - self.valeur_residuelle,
                    'valeur_residuelle': valeur_restante + self.valeur_residuelle,
                    'state': 'brouillon'
                })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tableau d\'amortissement',
            'view_mode': 'list,form',
            'res_model': 'it.parc.materiel.amortissement',
            'domain': [('materiel_id', '=', self.id)],
            'context': {'default_materiel_id': self.id},
        }

    def action_print_qrcode(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/image/qrcode?url={quote(self.qr_code_url)}&size=250',
            'target': 'new',
        }

# Création d'un nouveau modèle pour les lignes d'amortissement
class MaterielAmortissement(models.Model):
    _name = 'it.parc.materiel.amortissement'
    _description = 'Ligne d\'amortissement de matériel'
    _order = 'sequence, date_debut'
    
    materiel_id = fields.Many2one('it.parc.materiel', string='Matériel', required=True, ondelete='cascade')
    sequence = fields.Integer(string='N°', required=True)
    date_debut = fields.Date(string='Date de début', required=True)
    date_fin = fields.Date(string='Date de fin', required=True)
    montant = fields.Float(string='Montant', required=True)
    cumul = fields.Float(string='Cumul des amortissements')
    valeur_residuelle = fields.Float(string='Valeur résiduelle')
    state = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('comptabilise', 'Comptabilisé')
    ], string='État', default='brouillon', required=True)
    # Remplacer ce champ qui fait référence à account.move (comptabilité)
    # par un simple champ char ou boolean pour le moment
    ecriture_comptable_ref = fields.Char(string='Référence écriture comptable')
    
    def action_comptabiliser(self):
        """Comptabilise la ligne d'amortissement en créant une écriture comptable"""
        for ligne in self:
            if ligne.state == 'comptabilise':
                continue
            
            # Simplifier la fonction pour ne pas utiliser account.move
            # qui n'est pas disponible dans votre installation
            ligne.write({
                'state': 'comptabilise',
                'ecriture_comptable_ref': f"AMO/{fields.Date.today()}/{ligne.sequence}"
            })
            
            # Ajouter un message dans le chatter du matériel
            ligne.materiel_id.message_post(
                body=f"Amortissement {ligne.sequence} comptabilisé pour un montant de {ligne.montant}",
                subject=f"Comptabilisation amortissement"
            )
    
    @api.model
    def _cron_comptabiliser_amortissements(self):
        """CRON job pour comptabiliser automatiquement les amortissements à échéance"""
        today = fields.Date.today()
        # Trouver les lignes d'amortissement à échéance qui ne sont pas encore comptabilisées
        lignes = self.search([
            ('state', '=', 'brouillon'),
            ('date_fin', '<=', today)
        ])
        for ligne in lignes:
            try:
                ligne.action_comptabiliser()
            except Exception as e:
                _logger.error(f"Erreur lors de la comptabilisation de l'amortissement {ligne.id}: {e}")

class Site(models.Model):
    _name = 'it.parc.site'
    _description = 'Site'
    
    name = fields.Char(string='Nom du site', required=True)
    code = fields.Char(string='Code')
    adresse = fields.Text(string='Adresse')
    client_id = fields.Many2one('it.parc.client', string='Client')
    description = fields.Text(string='Description')


