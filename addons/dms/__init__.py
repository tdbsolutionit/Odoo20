import sys
import types

try:
    from odoo.osv import expression
except ImportError:
    from odoo.orm.domains import Domain

    osv = types.ModuleType("odoo.osv")
    expression = types.ModuleType("odoo.osv.expression")
    expression.OR = Domain.OR
    expression.AND = Domain.AND
    expression.NOT = Domain.NOT if hasattr(Domain, "NOT") else lambda d: ["!"] + list(d)
    expression.TRUE_DOMAIN = Domain.TRUE
    expression.FALSE_DOMAIN = Domain.FALSE
    expression.NEGATIVE_TERM_OPERATORS = Domain.NEGATIVE_OPERATORS
    expression.Domain = Domain
    expression.normalize_domain = lambda d: Domain(d)
    expression.is_leaf = Domain.is_condition

    osv.expression = expression
    sys.modules["odoo.osv"] = osv
    sys.modules["odoo.osv.expression"] = expression

from . import controllers
from . import models
from . import wizards
