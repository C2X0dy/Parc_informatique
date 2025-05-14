from odoo import http, fields, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import OR

class ItParcPortal(CustomerPortal):
    
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