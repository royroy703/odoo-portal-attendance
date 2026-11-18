from datetime import datetime, time
import pytz
from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalAttendanceController(CustomerPortal):

    def _get_employee(self):
        user = request.env.user
        return request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

    @http.route(['/my/attendance'], type='http', auth='user', website=True)
    def portal_my_attendance(self, **kw):
        employee = self._get_employee()
        if not employee:
            return request.render('portal_attendance.portal_no_employee')

        # Configurar zona horaria del usuario o por defecto Lima
        user_tz = pytz.timezone(request.env.user.tz or 'America/Lima')
        now_utc = fields.Datetime.now()
        now_local = pytz.utc.localize(now_utc).astimezone(user_tz)

        # Inicio de hoy en UTC
        today_start_local = user_tz.localize(datetime.combine(now_local.date(), time.min))
        today_start_utc = today_start_local.astimezone(pytz.utc).replace(tzinfo=None)

        # Primer día del mes en UTC
        first_day_month_local = user_tz.localize(datetime(now_local.year, now_local.month, 1, 0, 0, 0))
        first_day_month_utc = first_day_month_local.astimezone(pytz.utc).replace(tzinfo=None)

        Attendance = request.env['hr.attendance'].sudo()

        # Asistencias del mes para las métricas
        month_attendances = Attendance.search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', first_day_month_utc)
        ])

        today_attendances = month_attendances.filtered(lambda a: a.check_in >= today_start_utc)
        hours_today = sum(today_attendances.mapped('worked_hours'))
        hours_month = sum(month_attendances.mapped('worked_hours'))
        days_assisted = len(set(
            pytz.utc.localize(a.check_in).astimezone(user_tz).date()
            for a in month_attendances if a.check_in
        ))

        # Últimos 10 registros para el historial
        recent_attendances = Attendance.search([
            ('employee_id', '=', employee.id)
        ], order='check_in desc', limit=10)

        records = []
        for att in recent_attendances:
            cin = pytz.utc.localize(att.check_in).astimezone(user_tz) if att.check_in else None
            cout = pytz.utc.localize(att.check_out).astimezone(user_tz) if att.check_out else None
            records.append({
                'id': att.id,
                'date': cin.strftime('%d/%m/%Y') if cin else '—',
                'day_name': cin.strftime('%A') if cin else '',
                'check_in': cin.strftime('%H:%M:%S') if cin else '—',
                'check_out': cout.strftime('%H:%M:%S') if cout else 'En curso',
                'worked_hours': f"{att.worked_hours:.2f}" if att.worked_hours else '0.00',
                'is_active': not att.check_out,
            })

        values = self._prepare_portal_layout_values()
        values.update({
            'employee': employee,
            'attendance_state': employee.attendance_state,
            'hours_today': f"{hours_today:.2f}",
            'hours_month': f"{hours_month:.2f}",
            'days_assisted': days_assisted,
            'records': records,
            'page_name': 'attendance',
        })
        return request.render('portal_attendance.portal_my_attendance_view', values)

    @http.route(['/my/attendance/toggle'], type='http', auth='user', methods=['POST', 'GET'], website=True, csrf=False)
    def toggle_attendance(self, **post):
        employee = self._get_employee()
        if employee:
            Attendance = request.env['hr.attendance'].sudo()
            now = fields.Datetime.now()

            # Buscar si tiene un turno abierto (sin salida registrada)
            open_attendance = Attendance.search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False),
            ], limit=1, order='check_in desc')

            if open_attendance:
                # Marcar Salida (Check-Out)
                open_attendance.write({'check_out': now})
            else:
                # Marcar Entrada (Check-In)
                Attendance.create({
                    'employee_id': employee.id,
                    'check_in': now,
                })

        return request.redirect('/my/attendance')
    
    # ========================================================
    # NUEVA FUNCIÓN PARA EL PDF AGREGADA AQUÍ AL FINAL
    # ========================================================
    @http.route(['/my/attendance/download_pdf'], type='http', auth="user", website=True)
    def download_attendance_pdf(self, **kw):
        # 1. Buscar los últimos registros de asistencia del usuario actual
        domain = [('employee_id.user_id', '=', request.env.user.id)]
        attendances = request.env['hr.attendance'].sudo().search(domain, limit=10, order='check_in desc')
        
        if not attendances:
            return request.redirect('/my/attendance')

        # 2. Generar el documento PDF usando TU reporte QWeb (ID actualizado)
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'portal_attendance.action_report_attendance_custom', 
            [a.id for a in attendances]
        )
        
        # 3. Empaquetar y forzar la descarga en el navegador
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'attachment; filename="Historial_Marcaciones.pdf"')
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)