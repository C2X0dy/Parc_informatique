from odoo import http, fields, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import OR
from datetime import timedelta

class ItParcPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super(ItParcPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        # Rechercher le client associé au partenaire
        client = request.env['it.parc.client'].sudo().search([('partner_id', '=', partner.id)], limit=1)
        if client:
            values['client'] = client
        
        return values
    
    def _prepare_home_portal_values(self, counters):
        """Add IT Parc counters to portal home page"""
        values = super()._prepare_home_portal_values(counters)
        
        partner = request.env.user.partner_id
        
        if 'incident_count' in counters:
            incident_count = request.env['it.parc.incident'].search_count([
                ('client_id.partner_id', '=', partner.id)
            ])
            values['incident_count'] = incident_count
            
        if 'materiel_count' in counters:
            materiel_count = request.env['it.parc.materiel'].search_count([
                ('client_id.partner_id', '=', partner.id)
            ])
            values['materiel_count'] = materiel_count
            
        if 'contrat_count' in counters:
            contrat_count = request.env['it.parc.contrat'].search_count([
                ('client_id.partner_id', '=', partner.id)
            ])
            values['contrat_count'] = contrat_count
            
        if 'facture_count' in counters:
            facture_count = request.env['it.parc.facturation'].search_count([
                ('client_id.partner_id', '=', partner.id)
            ])
            values['facture_count'] = facture_count
    
        return values
    
    # Incident Portal
    @http.route(['/my/incidents', '/my/incidents/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_incidents(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        domain = [('client_id.partner_id', '=', partner.id)]
        
        # Count for statistics
        incidents_total = request.env['it.parc.incident'].search_count(domain)
        incidents_en_cours = request.env['it.parc.incident'].search_count(domain + [('etat', 'in', ['nouveau', 'en_cours'])])
        incidents_resolus = request.env['it.parc.incident'].search_count(domain + [('etat', '=', 'resolu')])
        
        # Pager
        page_limit = 10
        pager = portal_pager(
            url="/my/incidents",
            total=incidents_total,
            page=page,
            step=page_limit
        )
        
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date_creation desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'etat'},
        }
        
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']
        
        # Content
        incidents = request.env['it.parc.incident'].search(
            domain,
            limit=page_limit,
            offset=pager['offset'],
            order=sort_order
        )
        
        values.update({
            'incidents': incidents,
            'page_name': 'incidents',
            'pager': pager,
            'default_url': '/my/incidents',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'incidents_total': incidents_total,
            'incidents_en_cours': incidents_en_cours,
            'incidents_resolus': incidents_resolus,
        })
        
        return request.render("it_parc.portal_my_incidents", values)
    
    @http.route(['/my/incident/<int:incident_id>'], type='http', auth="user", website=True)
    def portal_incident_detail(self, incident_id, **kw):
        try:
            incident_sudo = self._document_check_access('it.parc.incident', incident_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = {
            'incident': incident_sudo,
            'page_name': 'incident',
        }
        
        return request.render("it_parc.portal_incident_detail", values)
    
    # Materiel Portal
    @http.route(['/my/materials', '/my/materials/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_materials(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        domain = [('client_id.partner_id', '=', partner.id)]
        
        # Count for statistics
        materials_total = request.env['it.parc.materiel'].search_count(domain)
        materials_actifs = request.env['it.parc.materiel'].search_count(domain + [('etat', '=', 'actif')])
        materials_maintenance = request.env['it.parc.materiel'].search_count(domain + [('etat', '=', 'maintenance')])
        
        # Pager
        page_limit = 10
        pager = portal_pager(
            url="/my/materials",
            total=materials_total,
            page=page,
            step=page_limit
        )
        
        searchbar_sortings = {
            'name': {'label': _('Name'), 'order': 'name'},
            'type': {'label': _('Type'), 'order': 'type'},
            'state': {'label': _('Status'), 'order': 'etat'},
        }
        
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']
        
        # Content
        materials = request.env['it.parc.materiel'].search(
            domain,
            limit=page_limit,
            offset=pager['offset'],
            order=sort_order
        )
        
        values.update({
            'materials': materials,
            'page_name': 'materials',
            'pager': pager,
            'default_url': '/my/materials',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'materials_total': materials_total,
            'materials_actifs': materials_actifs,
            'materials_maintenance': materials_maintenance,
        })
        
        return request.render("it_parc.portal_my_materials", values)
    
    @http.route(['/my/material/<int:materiel_id>'], type='http', auth="user", website=True)
    def portal_material_detail(self, materiel_id, **kw):
        try:
            materiel_sudo = self._document_check_access('it.parc.materiel', materiel_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = {
            'materiel': materiel_sudo,
            'page_name': 'material',
        }
        
        return request.render("it_parc.portal_material_detail", values)
    
    # Create an incident from the portal
    @http.route(['/my/create/incident'], type='http', auth="user", website=True)
    def portal_create_incident(self, **kw):
        partner = request.env.user.partner_id
        clients = request.env['it.parc.client'].search([('partner_id', '=', partner.id)])
        
        if not clients:
            return request.redirect('/my')
        
        client = clients[0]
        materiels = request.env['it.parc.materiel'].search([
            ('client_id', '=', client.id)
        ])
        
        values = {
            'page_name': 'create_incident',
            'client': client,
            'materiels': materiels,
            'types': [
                ('panne', _('Panne matérielle')),
                ('bug', _('Bug logiciel')),
                ('reseau', _('Problème réseau')),
                ('securite', _('Incident de sécurité')),
                ('demande', _('Demande d\'assistance')),
                ('autre', _('Autre'))
            ]
        }
        
        return request.render("it_parc.portal_create_incident", values)
    
    @http.route(['/my/incident/submit'], type='http', auth="user", website=True)
    def portal_submit_incident(self, **post):
        partner = request.env.user.partner_id
        clients = request.env['it.parc.client'].search([('partner_id', '=', partner.id)])
        
        if not clients:
            return request.redirect('/my')
        
        client = clients[0]
        
        # Create the incident
        vals = {
            'objet': post.get('objet'),
            'description': post.get('description'),
            'client_id': client.id,
            'type': post.get('type'),
            'priorite': '2',  # Normal priority
            'etat': 'nouveau',
        }
        
        if post.get('materiel_id'):
            vals['materiel_id'] = int(post.get('materiel_id'))
        
        incident = request.env['it.parc.incident'].sudo().create(vals)
        
        return request.redirect('/my/incident/%s' % incident.id)
    
    def _message_post_helper(self, res_model, res_id, message, **kwargs):
        """Helper method for posting messages in portal controllers"""
        if isinstance(res_id, str):
            res_id = int(res_id)
        return request.env[res_model].browse(res_id).sudo().message_post(
            body=message,
            message_type=kwargs.pop('message_type', 'comment'),
            **kwargs
        )
    
    @http.route(['/it_parc/qrcode'], type='http', auth="public")
    def generate_qrcode(self, data, **kw):
        import qrcode
        import io
        import base64
        
        # Generate QR code for the material page URL
        url = f"{request.httprequest.host_url}my/material/{data}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to binary for response
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        
        return request.make_response(
            output.read(),
            [('Content-Type', 'image/png')]
        )
    
    @http.route(['/my/dashboard'], type='http', auth="user", website=True)
    def portal_dashboard(self, **kw):
        partner = request.env.user.partner_id
        clients = request.env['it.parc.client'].sudo().search([('partner_id', '=', partner.id)])
        
        if not clients:
            return request.redirect('/my')
        
        client = clients[0]
        
        # Base statistics
        dashboard_data = {
            'client': client,
            'page_name': 'dashboard',
        }
        
        # Conditional widgets based on client preferences
        if client.widget_incident_stats:
            incidents_total = request.env['it.parc.incident'].search_count([('client_id', '=', client.id)])
            incidents_mois = request.env['it.parc.incident'].search_count([
                ('client_id', '=', client.id),
                ('date_creation', '>=', fields.Date.today() - timedelta(days=30))
            ])
            
            # Temps moyen de résolution
            incidents_resolus = request.env['it.parc.incident'].search([
                ('client_id', '=', client.id),
                ('etat', '=', 'resolu'),
                ('date_creation', '!=', False),
                ('date_cloture', '!=', False)
            ])
            
            temps_resolution = 0
            if incidents_resolus:
                somme_heures = sum([(inc.date_cloture - inc.date_creation).total_seconds() / 3600 for inc in incidents_resolus])
                temps_resolution = somme_heures / len(incidents_resolus)
                
            dashboard_data.update({
                'incidents_total': incidents_total,
                'incidents_mois': incidents_mois,
                'temps_resolution': temps_resolution,
            })
        
        if client.widget_equipment_stats:
            equipment_total = request.env['it.parc.materiel'].search_count([('client_id', '=', client.id)])
            equipment_active = request.env['it.parc.materiel'].search_count([
                ('client_id', '=', client.id),
                ('etat', '=', 'actif')
            ])
            equipment_maintenance = request.env['it.parc.materiel'].search_count([
                ('client_id', '=', client.id),
                ('etat', '=', 'maintenance')
            ])
            
            dashboard_data.update({
                'equipment_total': equipment_total,
                'equipment_active': equipment_active,
                'equipment_maintenance': equipment_maintenance,
            })
        
        if client.widget_contracts:
            contracts_total = request.env['it.parc.contrat'].search_count([('client_id', '=', client.id)])
            contracts_active = request.env['it.parc.contrat'].search_count([
                ('client_id', '=', client.id),
                ('etat', '=', 'actif')
            ])
            
            # Contracts expiring soon
            today = fields.Date.today()
            thirty_days_ahead = today + timedelta(days=30)
            contracts_expiring_soon = request.env['it.parc.contrat'].search_count([
                ('client_id', '=', client.id),
                ('etat', '=', 'actif'),
                ('date_fin', '>=', today),
                ('date_fin', '<=', thirty_days_ahead)
            ])
            
            dashboard_data.update({
                'contracts_total': contracts_total,
                'contracts_active': contracts_active,
                'contracts_expiring_soon': contracts_expiring_soon,
            })
        
        if client.widget_budget_forecast:
            # Simulation de données pour les prévisions budgétaires
            # Dans une implémentation réelle, cela viendrait d'un calcul basé sur les contrats et équipements
            current_year = fields.Date.today().year
            dashboard_data.update({
                'current_year_budget': 25000,
                'next_year_budget': 32000,
                'after_next_year_budget': 28000,
            })
        
        if client.widget_upcoming_events:
            # Récupérer les prochaines maintenances planifiées
            today = fields.Date.today()
            upcoming_maintenance = request.env['it.parc.maintenance'].search([
                ('client_id', '=', client.id),
                ('date_planifiee', '>=', today),
                ('etat', 'in', ['planifiee', 'en_cours'])
            ], limit=5, order='date_planifiee')
            
            dashboard_data.update({
                'upcoming_maintenance': upcoming_maintenance,
            })
        
        return request.render("it_parc.portal_dashboard", dashboard_data)
    
    @http.route(['/my/reports'], type='http', auth="user", website=True)
    def portal_reports(self, **kw):
        partner = request.env.user.partner_id
        clients = request.env['it.parc.client'].search([('partner_id', '=', partner.id)])
        
        if not clients:
            return request.redirect('/my')
        
        client = clients[0]
        
        return request.render("it_parc.portal_reports", {
            'client': client,
            'page_name': 'reports',
        })
    
    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_contracts(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        domain = [('client_id.partner_id', '=', partner.id)]
        
        # Statistiques
        contracts_total = request.env['it.parc.contrat'].search_count(domain)
        contracts_actifs = request.env['it.parc.contrat'].search_count(domain + [('etat', '=', 'actif')])
        
        # Contrats à renouveler (dans les 30 jours)
        today = fields.Date.today()
        thirty_days_ahead = today + timedelta(days=30)
        contracts_to_renew_count = request.env['it.parc.contrat'].search_count([
            ('client_id.partner_id', '=', partner.id),
            ('etat', '=', 'actif'),
            ('date_fin', '>=', today),
            ('date_fin', '<=', thirty_days_ahead)
        ])
        
        # Pager
        page_limit = 10
        pager = portal_pager(
            url="/my/contracts",
            total=contracts_total,
            page=page,
            step=page_limit
        )
        
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date_debut desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'etat'},
        }
        
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']
        
        # Content
        contracts = request.env['it.parc.contrat'].search(
            domain,
            limit=page_limit,
            offset=pager['offset'],
            order=sort_order
        )
        
        values.update({
            'contracts': contracts,
            'page_name': 'contracts',
            'pager': pager,
            'default_url': '/my/contracts',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'contracts_total': contracts_total,
            'contracts_actifs': contracts_actifs,
            'contracts_to_renew_count': contracts_to_renew_count,
        })
        
        return request.render("it_parc.portal_my_contracts", values)
    
    @http.route(['/my/contract/<int:contract_id>'], type='http', auth="user", website=True)
    def portal_contract_detail(self, contract_id, **kw):
        try:
            contrat_sudo = self._document_check_access('it.parc.contrat', contract_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        # Récupérer les matériels liés à ce contrat
        materiels = request.env['it.parc.materiel'].search([
            ('contrat_id', '=', contrat_sudo.id)
        ])
            
        values = {
            'contrat': contrat_sudo,
            'materiels': materiels,
            'page_name': 'contract',
        }
        
        return request.render("it_parc.portal_contract_detail", values)
    
    @http.route(['/my/invoices'], type='http', auth="user", website=True)
    def portal_my_invoices(self, **kw):
        # Implémentation de base
        return request.render("it_parc.portal_invoices", {
            'page_name': 'invoices',
        })
    
    @http.route(['/my/documents'], type='http', auth="user", website=True)
    def portal_documents(self, **kw):
        # Implémentation de base
        return request.render("it_parc.portal_documents", {
            'page_name': 'documents',
        })
    
    @http.route(['/my/settings'], type='http', auth="user", website=True)
    def portal_user_settings(self, **kw):
        """Page de paramètres utilisateur pour personnaliser l'expérience du portail"""
        partner = request.env.user.partner_id
        client = request.env['it.parc.client'].sudo().search([('partner_id', '=', partner.id)], limit=1)
        
        if not client:
            return request.redirect('/my')
        
        # Récupérer les thèmes prédéfinis
        themes = [
            {'id': 'theme_blue', 'name': 'Bleu Professionnel', 'primary': '#3c4ea0', 'secondary': '#28a745'},
            {'id': 'theme_green', 'name': 'Vert Nature', 'primary': '#2e7d32', 'secondary': '#1976d2'},
            {'id': 'theme_purple', 'name': 'Violet Élégant', 'primary': '#6a1b9a', 'secondary': '#ffc107'},
            {'id': 'theme_orange', 'name': 'Orange Dynamique', 'primary': '#e65100', 'secondary': '#2196f3'},
            {'id': 'theme_red', 'name': 'Rouge Passion', 'primary': '#c62828', 'secondary': '#607d8b'},
            {'id': 'theme_dark', 'name': 'Mode Sombre', 'primary': '#37474f', 'secondary': '#ff9800'},
        ]
        
        # Widgets disponibles pour le tableau de bord
        dashboard_widgets = [
            {'id': 'incident_stats', 'name': 'Statistiques des incidents', 'enabled': client.widget_incident_stats},
            {'id': 'equipment_stats', 'name': 'État du parc', 'enabled': client.widget_equipment_stats},
            {'id': 'budget_forecast', 'name': 'Prévisions budgétaires', 'enabled': client.widget_budget_forecast},
            {'id': 'contracts', 'name': 'Contrats actifs', 'enabled': client.widget_contracts},
            {'id': 'upcoming_events', 'name': 'Événements à venir', 'enabled': client.widget_upcoming_events},
            {'id': 'performance', 'name': 'Indicateurs de performance', 'enabled': client.widget_performance},
        ]
        
        # Préférences de notification
        notification_preferences = [
            {'id': 'ticket_created', 'name': 'Création de ticket', 'email': client.notify_ticket_created_email, 'sms': client.notify_ticket_created_sms},
            {'id': 'ticket_updated', 'name': 'Mise à jour de ticket', 'email': client.notify_ticket_updated_email, 'sms': client.notify_ticket_updated_sms},
            {'id': 'contract_expiry', 'name': 'Expiration de contrat', 'email': client.notify_contract_expiry_email, 'sms': client.notify_contract_expiry_sms},
            {'id': 'maintenance', 'name': 'Maintenance planifiée', 'email': client.notify_maintenance_email, 'sms': client.notify_maintenance_sms},
            {'id': 'invoice', 'name': 'Nouvelle facture', 'email': client.notify_invoice_email, 'sms': client.notify_invoice_sms},
        ]
        
        values = {
            'client': client,
            'page_name': 'settings',
            'themes': themes,
            'dashboard_widgets': dashboard_widgets,
            'notification_preferences': notification_preferences,
            'current_theme': next((t for t in themes if t['primary'] == client.couleur_primaire and t['secondary'] == client.couleur_secondaire), None)
        }
        
        return request.render("it_parc.portal_user_settings", values)

    @http.route(['/my/settings/save'], type='http', auth="user", website=True)
    def portal_save_settings(self, **post):
        """Enregistrer les paramètres utilisateur"""
        partner = request.env.user.partner_id
        client = request.env['it.parc.client'].sudo().search([('partner_id', '=', partner.id)], limit=1)
        
        if not client:
            return request.redirect('/my')
        
        # Mise à jour du thème
        if post.get('theme_id'):
            theme_id = post.get('theme_id')
            if theme_id == 'theme_blue':
                client.sudo().write({'couleur_primaire': '#3c4ea0', 'couleur_secondaire': '#28a745'})
            elif theme_id == 'theme_green':
                client.sudo().write({'couleur_primaire': '#2e7d32', 'couleur_secondaire': '#1976d2'})
            elif theme_id == 'theme_purple':
                client.sudo().write({'couleur_primaire': '#6a1b9a', 'couleur_secondaire': '#ffc107'})
            elif theme_id == 'theme_orange':
                client.sudo().write({'couleur_primaire': '#e65100', 'couleur_secondaire': '#2196f3'})
            elif theme_id == 'theme_red':
                client.sudo().write({'couleur_primaire': '#c62828', 'couleur_secondaire': '#607d8b'})
            elif theme_id == 'theme_dark':
                client.sudo().write({'couleur_primaire': '#37474f', 'couleur_secondaire': '#ff9800'})
            elif theme_id == 'theme_custom':
                # Thème personnalisé
                client.sudo().write({
                    'couleur_primaire': post.get('custom_primary_color', '#3c4ea0'),
                    'couleur_secondaire': post.get('custom_secondary_color', '#28a745')
                })
        
        # Mise à jour des widgets du tableau de bord
        client.sudo().write({
            'widget_incident_stats': post.get('widget_incident_stats') == 'on',
            'widget_equipment_stats': post.get('widget_equipment_stats') == 'on',
            'widget_budget_forecast': post.get('widget_budget_forecast') == 'on',
            'widget_contracts': post.get('widget_contracts') == 'on',
            'widget_upcoming_events': post.get('widget_upcoming_events') == 'on',
            'widget_performance': post.get('widget_performance') == 'on',
        })
        
        # Mise à jour des préférences de notification
        client.sudo().write({
            'notify_ticket_created_email': post.get('notify_ticket_created_email') == 'on',
            'notify_ticket_created_sms': post.get('notify_ticket_created_sms') == 'on',
            'notify_ticket_updated_email': post.get('notify_ticket_updated_email') == 'on',
            'notify_ticket_updated_sms': post.get('notify_ticket_updated_sms') == 'on',
            'notify_contract_expiry_email': post.get('notify_contract_expiry_email') == 'on',
            'notify_contract_expiry_sms': post.get('notify_contract_expiry_sms') == 'on',
            'notify_maintenance_email': post.get('notify_maintenance_email') == 'on',
            'notify_maintenance_sms': post.get('notify_maintenance_sms') == 'on',
            'notify_invoice_email': post.get('notify_invoice_email') == 'on',
            'notify_invoice_sms': post.get('notify_invoice_sms') == 'on',
        })
        
        return request.redirect('/my/settings?saved=1')

    # Ajouter cette méthode pour générer des documents personnalisés
    @http.route(['/my/document/preview/<string:doc_type>/<int:doc_id>'], type='http', auth="user", website=True)
    def portal_document_preview(self, doc_type, doc_id, **kw):
        """Preview d'un document avec le style personnalisé du client"""
        partner = request.env.user.partner_id
        client = request.env['it.parc.client'].sudo().search([('partner_id', '=', partner.id)], limit=1)
        
        if not client:
            return request.redirect('/my')
        
        try:
            if doc_type == 'contrat':
                document = self._document_check_access('it.parc.contrat', doc_id)
            elif doc_type == 'facture':
                document = self._document_check_access('it.parc.facturation', doc_id)
            elif doc_type == 'materiel':
                document = self._document_check_access('it.parc.materiel', doc_id)
            else:
                return request.redirect('/my')
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = {
            'client': client,
            'document': document,
            'doc_type': doc_type,
            'page_name': f'{doc_type}_preview',
        }
        
        return request.render(f"it_parc.portal_{doc_type}_preview", values)