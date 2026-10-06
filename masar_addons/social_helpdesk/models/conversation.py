from odoo import fields, models
from odoo.tools import plaintext2html


class SocialConversation(models.Model):
    _inherit = "social.conversation"

    ticket_id = fields.Many2one("helpdesk.ticket", check_company=True, groups="helpdesk_mgmt.group_helpdesk_user_own")

    def action_create_ticket(self):
        self.ensure_one()
        self.check_access("write")
        self.account_id._assert_operate()
        self.env.cr.execute("SELECT id FROM social_conversation WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset()
        if not self.ticket_id:
            incoming = self.delivery_ids.filtered(lambda d: d.direction == "incoming")[:1]
            ticket = self.env["helpdesk.ticket"].create({"name": self.name, "company_id": self.company_id.id, "partner_id": self.partner_id.id, "description": incoming.mail_message_id.body or plaintext2html(self.name)})
            self.write({"ticket_id": ticket.id})
            ticket.message_post(body=plaintext2html(f"Social source: {self.account_id.name}, conversation #{self.id}"), subtype_xmlid="mail.mt_note")
        self.ticket_id.check_access("read")
        return {"type": "ir.actions.act_window", "res_model": "helpdesk.ticket", "res_id": self.ticket_id.id, "view_mode": "form"}
