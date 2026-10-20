# -*- coding: utf-8 -*-
import logging
from odoo.tools.binary import BinaryBytes

_logger = logging.getLogger(__name__)

try:
    from odoo.orm.fields_binary import Binary
    _orig_convert_to_cache = Binary.convert_to_cache

    def _safe_convert_to_cache(self, value, records, validate=True):
        if isinstance(value, dict) and 'content' in value:
            filename = value.get('filename') or ''
            binary_value = self.convert_to_cache(value['content'], records, validate=validate)
            if filename and binary_value and getattr(binary_value, 'filename', None) != filename:
                binary_value = BinaryBytes(binary_value.content, filename=filename)
            return binary_value
        return _orig_convert_to_cache(self, value, records, validate=validate)

    Binary.convert_to_cache = _safe_convert_to_cache
    _logger.info("Successfully applied safe patch to odoo.orm.fields_binary.Binary.convert_to_cache")
except Exception as e:
    _logger.warning("Could not patch Binary.convert_to_cache: %s", e)
