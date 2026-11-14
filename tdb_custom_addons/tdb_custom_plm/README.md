# Omnia CAD database discovery

`POST /xmlrpc/db` accepts XML-RPC methods `list` and `list_db` and always
returns `['odoo_dev']`. Other methods return an XML-RPC fault. This endpoint
does not query PostgreSQL or provide database administration operations.

Add the parent `tdb_custom_addons` directory to `addons_path`. Install this
module on `odoo_dev` and add it to the existing server-wide module list so
the route is available before a database has been selected, for example:

```ini
server_wide_modules = base,web,rpc,tdb_custom_plm
```

Alternatively, use `--load=base,web,rpc,tdb_custom_plm`. Preserve any other
server-wide modules required by your deployment, then restart Odoo.

For this workspace, append `C:\Odoo20.0\odoo\tdb_custom_addons` to the
existing `addons_path`. Neither `odoo.conf` nor `odoo_8070.conf` currently
includes this directory. Select the configuration used by your actual
`odoo_dev` server; `odoo_8070.conf` targets a different database.

Loading this module server-wide makes database discovery available even
without a selected database. Installing it alone does not ensure discovery
works before login.

## PLM Documents default filter

This module depends on `plm` and updates `plm.plm_action_document_form` so
Documents opens without the **Must Update from CAD** filter selected.
The filter remains available for manual selection, and the `odooPLM`
context is preserved.

After deploying these files, restart Odoo and install or upgrade
`tdb_custom_plm` in the target database through Apps. Reload the browser
and reopen PLM > Documents to apply the updated action.

Only `/xmlrpc/db` is provided here. `/xmlrpc/2/db` and `/jsonrpc` are not
extended. The fixed name is returned even if `odoo_dev` does not exist or
`list_db` is disabled; it does not verify availability or grant login access.

Verify against the running server (adjust the URL/port):

```python
from xmlrpc.client import ServerProxy

db = ServerProxy('http://localhost:8069/xmlrpc/db')
assert db.list() == ['odoo_dev']
assert db.list_db() == ['odoo_dev']
```

Use `odoo_dev` as the database in Omnia CAD. Authentication and model calls
continue through Odoo's existing RPC endpoints.
