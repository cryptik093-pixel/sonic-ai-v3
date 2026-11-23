"""Read-only commerce qualification from a captured snapshot; never calls Shopify.

Evidence is accepted only as supplied structured observations, not independently
verified by this tool. A qualified report is not authorization to publish.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

BUNDLES = {
    '15471014510828': {'price': '40.00', 'components': ['lord_of_prudence', 'studio_guitar_collection']},
    '15471014543596': {'price': '60.00', 'components': ['lord_of_prudence', 'studio_guitar_collection', 'adlib93', 'premiere_drum_kit']},
}
REQUIRED_GATES = ('delivery', 'license', 'checkout')


def _id(value):
    return str(value or '').rsplit('/', 1)[-1]


def _nodes(value):
    if isinstance(value, list):
        return [x.get('node', x) if isinstance(x, dict) else x for x in value]
    if isinstance(value, dict):
        return _nodes(value.get('nodes', value.get('edges', [])))
    return []


def _money(value):
    if isinstance(value, dict):
        value = value.get('amount')
    if isinstance(value, bool) or value is None:
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return amount if amount.is_finite() and amount >= 0 else None


def _image(product):
    def present(value):
        if isinstance(value, str):
            return value.startswith(('https://', 'http://'))
        if isinstance(value, dict):
            return any(present(value.get(k)) for k in ('url', 'image', 'preview'))
        return False
    return any(present(product.get(k)) for k in ('featuredImageUrl', 'imageUrl', 'featuredImage', 'featuredMedia')) or any(present(x) for x in _nodes(product.get('images', [])))


def _variants(product):
    return _nodes(product.get('variants', []))


def _price(product):
    variants = _variants(product)
    prices = [_money(v.get('price')) for v in variants if isinstance(v, dict)]
    if variants:
        # All offers on a bundle must preserve its approved price.
        return prices
    price_range = product.get('priceRangeV2') or {}
    raw = product.get('price', price_range.get('minVariantPrice') if isinstance(price_range, dict) else None)
    return [_money(raw)]


def _evidence(record, product_id):
    """Require a typed observed assertion with subject binding and content hash."""
    if not isinstance(record, dict):
        return False
    try:
        observed = datetime.fromisoformat(str(record.get('observed_at', '')).replace('Z', '+00:00'))
        if observed.tzinfo is None:
            return False
    except ValueError:
        return False
    return (record.get('passed') is True and
            record.get('validation_status') == 'observed' and
            _id(record.get('subject_product_id')) == product_id and
            isinstance(record.get('evidence_ref'), str) and bool(record['evidence_ref'].strip()) and
            isinstance(record.get('sha256'), str) and
            re.fullmatch(r'[a-fA-F0-9]{64}', record['sha256']) is not None and
            isinstance(record.get('observed_at'), str) and
            re.fullmatch(r'\d{4}-\d{2}-\d{2}T[^ ]+(?:Z|[+-]\d{2}:\d{2})', record['observed_at']) is not None)


def _filename(file):
    literal = file.get('filename') or file.get('name')
    if literal:
        return unquote(str(literal).replace('\\', '/').rsplit('/', 1)[-1])
    source = file.get('originalSource')
    source = source if isinstance(source, dict) else {}
    raw = file.get('url') or source.get('url') or ''
    return unquote(urlsplit(str(raw)).path.rsplit('/', 1)[-1])


def _key(label):
    # Restrict recognition to explicit minor labels; filenames alone cannot prove audio key.
    match = re.search(r'(?<![a-zA-Z])([A-Ga-g])\s*(#|♯|b|♭|sharp|flat)?[ _-]*(?:minor|min)(?![a-zA-Z])', unquote(label), re.I)
    if not match:
        return None
    accidental = {'sharp': '#', '♯': '#', 'flat': 'b', '♭': 'b'}.get((match[2] or '').lower(), match[2] or '')
    return match[1].upper() + accidental + ' minor'


def _words(value):
    return re.sub(r'[^a-z0-9]+', '', value.lower())


def _label_mismatches(products, files):
    results = []
    for product in products:
        title = str(product.get('title', ''))
        expected = _key(title)
        if expected is None:
            continue
        # Match a real product handle or its name before a musical-key separator.
        name = re.split(r'\s[—–|]\s', title)[0]
        if _key(name):
            name = re.sub(r'(?i)\b[A-G](?:#|b)?[ _-]*(?:minor|min)\b.*', '', name).strip(' -_')
        name = re.sub(r'(?i)^Detroit[ _-]+', '', name)
        tokens = [_words(name), _words(str(product.get('handle', '')))]
        tokens = [x for x in tokens if len(x) >= 5]
        for file in files:
            filename = _filename(file)
            linked = _id(file.get('product_id')) == _id(product.get('id')) and bool(file.get('product_id'))
            if not linked and not any(token in _words(filename) for token in tokens):
                continue
            actual = _key(filename)
            if actual and actual != expected:
                results.append({'product_id': _id(product.get('id')), 'product_title': title,
                                'filename': filename, 'product_label': expected, 'file_label': actual,
                                'finding': 'metadata_label_mismatch', 'audio_key_verified': False})
    return sorted(results, key=lambda x: (x['product_id'], x['filename']))


def audit(snapshot):
    if not isinstance(snapshot, dict):
        raise ValueError('Snapshot must be a JSON object.')
    groups = {}
    for field in ('products', 'themes', 'files'):
        value = snapshot.get(field, [])
        if not isinstance(value, list):
            raise ValueError(field + ' must be a list.')
        groups[field] = _nodes(value)
        if not all(isinstance(item, dict) for item in groups[field]):
            raise ValueError(field + ' must contain objects.')
    evidence = snapshot.get('verified_delivery', {})
    if not isinstance(evidence, dict):
        raise ValueError('verified_delivery must be an object.')
    products = groups['products']
    by_id = {}
    for product in products:
        ident = _id(product.get('id'))
        if ident:
            if ident in by_id:
                raise ValueError('Duplicate product identity: ' + ident)
            by_id[ident] = product
    reports = []
    for ident, approved in BUNDLES.items():
        product = by_id.get(ident)
        blockers = []
        checks = {'product_present': product is not None}
        supplied = evidence.get(ident, evidence.get('gid://shopify/Product/' + ident, {}))
        if not isinstance(supplied, dict):
            supplied = {}
        if product is None:
            blockers.append('product_missing')
        else:
            prices = _price(product)
            checks['approved_price'] = bool(prices) and all(x == Decimal(approved['price']) for x in prices)
            price_range = product.get('priceRangeV2')
            price_range = price_range if isinstance(price_range, dict) else {}
            minimum = price_range.get('minVariantPrice')
            minimum = minimum if isinstance(minimum, dict) else {}
            currencies = [code for code in (product.get('currencyCode'), minimum.get('currencyCode')) if code is not None]
            checks['currency_usd'] = bool(currencies) and all(code == 'USD' for code in currencies)
            checks['image_present'] = _image(product)
            variants = _variants(product)
            checks['sku_present'] = bool(variants) and all(isinstance(v, dict) and isinstance(v.get('sku'), str) and bool(v['sku'].strip()) for v in variants)
            for key in ('approved_price', 'currency_usd', 'image_present', 'sku_present'):
                if not checks[key]:
                    blockers.append(key + '_unverified_or_mismatch')
        # Component identity requires explicit typed manifests, never inferred marketing prose.
        components = supplied.get('components')
        checks['approved_components'] = (isinstance(components, list) and
            sorted(components) == sorted(approved['components']) if
            isinstance(components, list) and all(isinstance(x, str) for x in components) else False)
        if not checks['approved_components']:
            blockers.append('component_manifest_missing_or_mismatch')
        for gate in REQUIRED_GATES:
            checks[gate] = _evidence(supplied.get(gate), ident)
            if not checks[gate]:
                blockers.append(gate + '_evidence_missing_or_invalid')
        if 'adlib93' in approved['components']:
            kind = supplied.get('adlib93_asset_kind')
            checks['adlib93_identity_resolved'] = kind in ('audio_asset', 'plugin_binary')
            if not checks['adlib93_identity_resolved']:
                blockers.append('adlib93_asset_identity_unresolved')
            if kind == 'plugin_binary':
                for gate in ('build', 'dsp', 'state', 'host', 'cpu', 'design'):
                    checks['plugin_' + gate] = _evidence(supplied.get('plugin_' + gate), ident)
                    if not checks['plugin_' + gate]:
                        blockers.append('plugin_' + gate + '_evidence_missing_or_invalid')
        reports.append({'product_id': ident, 'approved_price_usd': approved['price'],
                        'approved_components': approved['components'], 'checks': checks,
                        'blockers': blockers, 'qualified_from_supplied_evidence': not blockers})
    themes = [{'id': _id(t.get('id')), 'name': str(t.get('name', '')), 'role': str(t.get('role', '')),
               'production_mutation_prohibited': str(t.get('role', '')).upper() == 'MAIN'}
              for t in groups['themes']]
    mismatches = _label_mismatches(products, groups['files'])
    blockers = []
    for bundle in reports:
        product_findings = [finding for finding in mismatches if finding['product_id'] == bundle['product_id']]
        bundle['metadata_findings'] = product_findings
        if product_findings:
            bundle['blockers'].append('metadata_label_mismatch')
            bundle['qualified_from_supplied_evidence'] = False
    if not all(x['qualified_from_supplied_evidence'] for x in reports):
        blockers.append('bundle_qualification_incomplete')
    return {'report_version': 1, 'mode': 'read_only_snapshot_audit', 'bundles': reports,
            'themes': sorted(themes, key=lambda x: x['id']), 'metadata_findings': mismatches,
            'catalog_metadata_review_required': bool(mismatches),
            'qualified_from_supplied_evidence': not blockers, 'blockers': blockers,
            'production_approval': False,
            'limitations': ['Supplied evidence references and hashes are structurally validated, not independently authenticated.',
                            'Zero inventory does not establish sold-out status without inventory policy and tracking evidence.',
                            'Filename/product key differences are label mismatches, not measured audio-key findings.',
                            'Missing catalog pages, files or themes cannot be reconstructed from this snapshot.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--require-qualified', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = audit(json.loads(args.snapshot.read_text(encoding='utf-8')))
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'error': str(exc), 'qualified_from_supplied_evidence': False}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if args.require_qualified and not result['qualified_from_supplied_evidence'] else 0


if __name__ == '__main__':
    sys.exit(main())
