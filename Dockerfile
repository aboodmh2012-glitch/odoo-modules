FROM odoo:20.0

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/lib/odoo /mnt/extra-addons

COPY --chown=odoo:odoo odoo20/odoo.conf /etc/odoo/odoo.conf
COPY odoo20/start.sh /start.sh
RUN chmod 755 /start.sh

# MASAR-compatible addons live under masar_addons/ (COPY from MASAR, never move).
# Blue Fox / unrelated Odoo 18 trees are NOT baked into the Odoo 20 image.
COPY --chown=odoo:odoo masar_addons/ /mnt/extra-addons/

USER root
ENTRYPOINT ["/start.sh"]
EXPOSE 8069
