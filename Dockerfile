FROM odoo:20.0
USER root
RUN apt-get update && apt-get install -y --no-install-recommends gosu && rm -rf /var/lib/apt/lists/*  && mkdir -p /var/lib/odoo /mnt/extra-addons /opt/masar
COPY --chown=odoo:odoo odoo20/odoo.conf /etc/odoo/odoo.conf
COPY --chown=odoo:odoo odoo20/seed_masar_reference.py /opt/masar/seed_masar_reference.py
# MASAR non-HR addons first (COPY from smartexsoftorg/masar — never edit MASAR in place).
# HR/employee modules deferred until explicit go-ahead.
COPY --chown=odoo:odoo masar_addons/ /mnt/extra-addons/
COPY odoo20/start.sh /start.sh
RUN chmod 755 /start.sh
USER root
ENTRYPOINT ["/start.sh"]
EXPOSE 8069
