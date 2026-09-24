# Odoo 18 Community + Symbifox extra addons (baked into the image).
# Deploy on Railway service "Odoo" for project smart — do not change major version.
FROM odoo:18.0

USER root

# System deps sometimes needed by module Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
# Official Odoo image is Debian-based; pip may need --break-system-packages on newer Python.
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt \
    || pip3 install --no-cache-dir -r /tmp/requirements.txt

# Custom modules live at the path already expected by this stack.
COPY --chown=odoo:odoo . /mnt/extra-addons/

# Drop non-addon clutter that may have been copied before .dockerignore applied in local builds.
RUN find /mnt/extra-addons -maxdepth 1 -type f \
        \( -name 'Dockerfile' -o -name 'docker-compose*' -o -name 'railway.toml' \
           -o -name 'requirements.txt' -o -name 'ruff.toml' -o -name '.gitignore' \) \
        -delete \
    && rm -rf /mnt/extra-addons/deploy /mnt/extra-addons/tools /mnt/extra-addons/.github \
    && chown -R odoo:odoo /mnt/extra-addons /var/lib/odoo

COPY --chown=odoo:odoo deploy/odoo.conf /etc/odoo/odoo.conf

USER odoo

EXPOSE 8069 8072
