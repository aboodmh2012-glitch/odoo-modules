# Odoo 18 Community + Symbifox extra addons (baked into the image).
# Deploy on Railway service "odoo" for project smart — do not change major version.
FROM odoo:18.0

USER root

# Only install runtime helpers. Do NOT pip-upgrade cryptography/lxml/requests:
# those are Debian-managed in the Odoo image and upgrading them breaks pyOpenSSL.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*

# Optional Python deps that are NOT shipped by the Odoo image.
# Keep this list narrow; never list cryptography/PyPDF2/lxml/requests/reportlab here.
COPY deploy/requirements-extra.txt /tmp/requirements-extra.txt
# Install extras without replacing Debian-managed packages from the Odoo image.
# pywebpush 1.14.1 works with the image cryptography; --ignore-installed avoids
# pip trying to uninstall Debian packages that have no pip RECORD metadata.
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed -r /tmp/requirements-extra.txt

# Custom modules baked at build time (no git clone on restart).
COPY --chown=odoo:odoo . /mnt/extra-addons/
RUN find /mnt/extra-addons -maxdepth 1 -type f \
        \( -name 'Dockerfile' -o -name 'docker-compose*' -o -name 'railway.toml' \
           -o -name 'requirements.txt' -o -name 'ruff.toml' -o -name '.gitignore' \) \
        -delete \
    && rm -rf /mnt/extra-addons/deploy /mnt/extra-addons/tools /mnt/extra-addons/.github \
    && mkdir -p /var/lib/odoo \
    && chown -R odoo:odoo /mnt/extra-addons /var/lib/odoo

COPY deploy/odoo.conf /etc/odoo/odoo.conf
COPY deploy/railway-entrypoint.sh /railway-entrypoint.sh
COPY deploy/railway-odoo-start.sh /railway-odoo-start.sh
RUN chmod 755 /railway-entrypoint.sh /railway-odoo-start.sh \
    && chown odoo:odoo /etc/odoo/odoo.conf

# Stay root so the entrypoint can chown the Railway volume, then drop to odoo.
USER root
ENTRYPOINT ["/railway-entrypoint.sh"]
CMD []

EXPOSE 8069 8072
