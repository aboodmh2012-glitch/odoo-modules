def post_init_hook(env):
    """Keep the public site identity aligned with the copy catalog."""
    env["website"].masar_apply_public_identity()
