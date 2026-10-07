from odoo import fields, models
from odoo.tools import plaintext2html


class SocialConversation(models.Model):
    _inherit = "social.conversation"

    lead_id = fields.Many2one("crm.lead", check_company=True, groups="sales_team.group_sale_salesman")

    def _create_crm_record(self, kind):
        self.ensure_one()
        self.check_access("write")
        self.account_id._assert_operate()
        self.env.cr.execute("SELECT id FROM social_conversation WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset()
        if not self.lead_id:
            incoming = self.delivery_ids.filtered(lambda d: d.direction == "incoming")[:1]
            lead = self.env["crm.lead"].create({"name": self.name, "type": kind, "company_id": self.company_id.id, "partner_id": self.partner_id.id, "description": incoming.mail_message_id.body or plaintext2html(self.name)})
            self.write({"lead_id": lead.id})
            lead.message_post(body=plaintext2html(f"Social source: {self.account_id.name}, conversation #{self.id}"), subtype_xmlid="mail.mt_note")
        self.lead_id.check_access("read")
        return {"type": "ir.actions.act_window", "res_model": "crm.lead", "res_id": self.lead_id.id, "view_mode": "form"}

    def action_create_lead(self):
        return self._create_crm_record("lead")

    def action_create_opportunity(self):
        return self._create_crm_record("opportunity")
