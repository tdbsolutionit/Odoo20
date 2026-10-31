FROM odoobot/odoo:20.0

USER root

# Install LibreOffice headless & fonts for document preview conversions
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer-nogui \
    libreoffice-calc-nogui \
    libreoffice-impress-nogui \
    fonts-dejavu \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Clone Odoo 20 source code (shallow clone for fastest build)
RUN git clone --depth 1 --branch 20.0 https://github.com/odoo/odoo.git /opt/odoo/src \
    && chown -R odoo:odoo /opt/odoo/src \
    && /opt/odoo/venv/bin/pip install --no-cache-dir -e /opt/odoo/src

# Create extra-addons directory and data directory
RUN mkdir -p /mnt/extra-addons /var/lib/odoo \
    && chown -R odoo:odoo /mnt/extra-addons /var/lib/odoo

USER odoo

EXPOSE 8069 8072

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/opt/odoo/venv/bin/python3", "/opt/odoo/src/odoo-bin", "-c", "/etc/odoo/odoo.conf"]
