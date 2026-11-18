/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

// 1. Lógica del Reloj
publicWidget.registry.PortalAttendanceClock = publicWidget.Widget.extend({
    selector: '.craft-clock-box',
    
    start: function () {
        this.timeElement = this.el.querySelector('.digital-time');
        this.dateElement = this.el.querySelector('.digital-date');
        
        this._updateClock();
        this.clockInterval = setInterval(this._updateClock.bind(this), 1000);
        return this._super.apply(this, arguments);
    },

    destroy: function () {
        clearInterval(this.clockInterval);
        this._super.apply(this, arguments);
    },

    _updateClock: function () {
        const now = new Date();
        
        let hours = now.getHours();
        let minutes = now.getMinutes();
        let seconds = now.getSeconds();
        const ampm = hours >= 12 ? 'p.m.' : 'a.m.';
        
        hours = hours % 12;
        hours = hours ? hours : 12;
        
        const strHours = hours.toString().padStart(2, '0');
        const strMinutes = minutes.toString().padStart(2, '0');
        const strSeconds = seconds.toString().padStart(2, '0');
        
        const timeString = `${strHours}:${strMinutes}:${strSeconds} ${ampm}`;

        const dateString = now.toLocaleDateString('es-PE', {
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric'
        });

        if (this.timeElement) {
            this.timeElement.textContent = timeString;
        }
        if (this.dateElement) {
            this.dateElement.textContent = dateString.charAt(0).toUpperCase() + dateString.slice(1);
        }
    }
});

// 2. Lógica del Botón Check-in / Check-out sin RPC
publicWidget.registry.PortalAttendanceBtn = publicWidget.Widget.extend({
    selector: '#btn_toggle_attendance',
    events: {
        'click': '_onClickToggle',
    },

    _onClickToggle: function (ev) {
        ev.preventDefault();
        const btn = ev.currentTarget;
        btn.disabled = true;
        
        // Opcional: Cambiar el texto mientras procesa
        if (btn.querySelector('span')) {
            btn.querySelector('span').textContent = 'Procesando...';
        } else {
            btn.textContent = 'Procesando...';
        }
        
        // Redirige directamente al controlador de Python
        window.location.href = '/my/attendance/toggle';
    }
});