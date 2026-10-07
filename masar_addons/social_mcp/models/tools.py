from odoo import api, models
from odoo.exceptions import AccessError
from odoo.addons.mcp_server.models.mcp_mixin import mcp_tool


class SocialMcpTools(models.AbstractModel):
    _inherit = "mcp.mixin"

    @mcp_tool(name="social_create_draft", description="Create a Social draft only. Does not approve, schedule or publish.", operation="create", input_schema={"type": "object", "properties": {"name": {"type": "string", "maxLength": 200}, "content": {"type": "string", "maxLength": 16000}, "company_id": {"type": "integer"}}, "required": ["name", "content", "company_id"], "additionalProperties": False}, readOnlyHint=False, destructiveHint=False)
    @api.model
    def social_create_draft(self, name, content, company_id):
        model = self._resolve_model("social.post")
        self._check_op("social.post", "create")
        if company_id not in self.env.companies.ids:
            raise AccessError("Select an allowed company first.")
        post = model.create({"name": name[:200], "content": content[:16000], "company_id": company_id})
        return {"id": post.id, "state": post.state}

    @mcp_tool(name="social_work_summary", description="Read Social post status counts and conversations requiring a reply, within caller permissions.", operation="read", input_schema={"type": "object", "properties": {}, "additionalProperties": False}, readOnlyHint=True)
    @api.model
    def social_work_summary(self):
        posts = self._resolve_model("social.post")
        self._check_op("social.post", "read")
        conversations = self._resolve_model("social.conversation")
        self._check_op("social.conversation", "read")
        return {"posts": posts.read_group([], ["state"], ["state"]), "needs_reply": conversations.search_count([("needs_reply", "=", True), ("spam", "=", False)])}

    @mcp_tool(name="social_request_review", description="Request review of an existing Social draft. Does not approve or publish.", operation="write", input_schema={"type": "object", "properties": {"post_id": {"type": "integer"}}, "required": ["post_id"], "additionalProperties": False}, readOnlyHint=False)
    @api.model
    def social_request_review(self, post_id):
        posts = self._resolve_model("social.post")
        self._check_op("social.post", "write")
        post = posts.browse(post_id)
        post.action_request_review()
        return {"id": post.id, "state": post.state}
