FROM odoo:20.0
USER root
RUN mkdir -p /var/lib/odoo /mnt/extra-addons && chown -R odoo:odoo /var/lib/odoo /mnt/extra-addons
COPY --chown=odoo:odoo odoo.conf /etc/odoo/odoo.conf
COPY --chown=odoo:odoo start.sh /start.sh
RUN chmod 755 /start.sh
USER odoo
ENTRYPOINT ["/start.sh"]
EXPOSE 8069
