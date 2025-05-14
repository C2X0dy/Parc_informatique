odoo.define('it_parc.portal_animations', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    
    publicWidget.registry.ITPortalAnimations = publicWidget.Widget.extend({
        selector: '.o_portal_wrap',
        events: {
            'click .ai-assistant-toggle': '_onToggleAssistant',
            'click .ai-assistant-close': '_onCloseAssistant',
        },
        
        /**
         * @override
         */
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._initializeAnimations();
                self._initializeTooltips();
                if ($('.chart-container').length) {
                    self._initializeCharts();
                }
            });
        },
        
        /**
         * Initialize entrance animations for dashboard elements
         */
        _initializeAnimations: function () {
            // Add entrance animation to cards
            $('.dashboard-card, .card').each(function(index) {
                $(this).css({
                    'animation': 'fadeInUp 0.5s ease forwards',
                    'animation-delay': (index * 0.1) + 's',
                    'opacity': 0,
                    'transform': 'translateY(20px)'
                });
            });
            
            // Add custom CSS animation if not already in the page
            if (!$('#portal-animations-css').length) {
                $('head').append(
                    '<style id="portal-animations-css">' +
                    '@keyframes fadeInUp {' +
                    '  from { opacity: 0; transform: translateY(20px); }' +
                    '  to { opacity: 1; transform: translateY(0); }' +
                    '}' +
                    '@keyframes pulse {' +
                    '  from { transform: scale(1); }' +
                    '  50% { transform: scale(1.05); }' +
                    '  to { transform: scale(1); }' +
                    '}' +
                    '</style>'
                );
            }
            
            // Add hover effects to buttons
            $('.btn').hover(
                function() {
                    $(this).css('transform', 'translateY(-2px)');
                },
                function() {
                    $(this).css('transform', 'translateY(0)');
                }
            );
            
            // Pulse animation for important elements
            setInterval(function() {
                $('.ai-assistant-toggle').css('animation', 'pulse 1s infinite');
            }, 5000);
        },
        
        /**
         * Initialize Bootstrap tooltips
         */
        _initializeTooltips: function () {
            $('[data-bs-toggle="tooltip"]').tooltip();
        },
        
        /**
         * Initialize charts if Chart.js is available
         * This is a simple placeholder - in a real implementation,
         * you would load actual data from your controller
         */
        _initializeCharts: function () {
            if (typeof Chart === 'undefined') {
                console.log('Chart.js not loaded, skipping chart initialization');
                return;
            }
            
            var ctx = $('.chart-container').find('canvas');
            if (!ctx.length) {
                $('.chart-container').append('<canvas id="incidentsChart"></canvas>');
                ctx = $('#incidentsChart');
            }
            
            // Sample data
            var chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Incidents',
                        data: [5, 8, 3, 7, 4, 6],
                        borderColor: '#3c4ea0',
                        backgroundColor: 'rgba(60, 78, 160, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        },
        
        /**
         * Toggle AI assistant panel
         */
        _onToggleAssistant: function (ev) {
            ev.preventDefault();
            var $panel = $('.ai-assistant-panel');
            $panel.toggleClass('d-none');
            
            if (!$panel.hasClass('d-none')) {
                this._focusAssistantInput();
            }
        },
        
        /**
         * Close AI assistant panel
         */
        _onCloseAssistant: function (ev) {
            ev.preventDefault();
            $('.ai-assistant-panel').addClass('d-none');
        },
        
        /**
         * Focus on assistant input field
         */
        _focusAssistantInput: function () {
            setTimeout(function() {
                $('.ai-chat-input input').focus();
            }, 100);
        }
    });
    
    return publicWidget.registry.ITPortalAnimations;
});