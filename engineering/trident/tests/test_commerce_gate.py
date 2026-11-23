"""Deterministic contract and failure-path tests for the snapshot auditor."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).parents[1] / 'tools' / 'commerce_gate.py'
spec = importlib.util.spec_from_file_location('commerce_gate', MODULE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def evidence(ident):
    return {'passed': True, 'validation_status': 'observed', 'subject_product_id': ident,
            'evidence_ref': 'evidence/check.json', 'sha256': 'a' * 64,
            'observed_at': '2026-10-25T00:00:00-05:00'}


def qualified_fixture():
    snapshot = {'currencyCode': 'USD', 'products': [], 'themes': [], 'files': [], 'verified_delivery': {}}
    for ident, contract in gate.BUNDLES.items():
        snapshot['products'].append({'id': 'gid://shopify/Product/' + ident,
            'title': 'Bundle', 'currencyCode': 'USD', 'featuredImageUrl': 'https://example.test/image.png',
            'variants': [{'id': 'v1', 'sku': 'BUNDLE-' + ident, 'price': contract['price'], 'inventoryQuantity': 0}]})
        supplied = {'components': contract['components'], 'adlib93_asset_kind': 'audio_asset'}
        supplied.update({key: evidence(ident) for key in gate.REQUIRED_GATES})
        snapshot['verified_delivery'][ident] = supplied
    return snapshot


class CommerceGateTests(unittest.TestCase):
    def test_incomplete_snapshot_fails_closed(self):
        report = gate.audit({})
        self.assertFalse(report['qualified_from_supplied_evidence'])
        self.assertTrue(all('product_missing' in x['blockers'] for x in report['bundles']))
        self.assertFalse(report['production_approval'])

    def test_malformed_shape_and_duplicate_identity_rejected(self):
        for snapshot in ([], {'products': {}}, {'themes': ['bad']}, {'verified_delivery': []}):
            with self.subTest(snapshot=snapshot), self.assertRaises(ValueError):
                gate.audit(snapshot)
        fixture = qualified_fixture()
        fixture['products'].append(fixture['products'][0])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            gate.audit(fixture)

    def test_exact_decimal_price_and_zero_inventory_do_not_block(self):
        fixture = qualified_fixture()
        fixture['products'][0]['variants'][0]['price'] = '40.000'
        report = gate.audit(fixture)
        self.assertTrue(report['qualified_from_supplied_evidence'])
        self.assertNotIn('sold_out', json.dumps(report))
        self.assertIn('Zero inventory', report['limitations'][1])

    def test_currency_mismatch_or_missing_blocks_qualification(self):
        for currency in ('CAD', None):
            fixture = qualified_fixture()
            fixture['products'][0]['currencyCode'] = currency
            self.assertFalse(gate.audit(fixture)['bundles'][0]['checks']['currency_usd'])

    def test_conflicting_currency_rejected_and_price_range_usd_accepted(self):
        fixture = qualified_fixture()
        product = fixture['products'][0]
        product['priceRangeV2'] = {'minVariantPrice': {'amount': '40.00', 'currencyCode': 'EUR'}}
        self.assertFalse(gate.audit(fixture)['bundles'][0]['checks']['currency_usd'])
        product['priceRangeV2']['minVariantPrice']['currencyCode'] = 'USD'
        product.pop('currencyCode')
        self.assertTrue(gate.audit(fixture)['bundles'][0]['checks']['currency_usd'])
        product['currencyCode'] = 'EUR'
        self.assertFalse(gate.audit(fixture)['bundles'][0]['checks']['currency_usd'])

    def test_wrong_price_and_invalid_numbers_fail_closed(self):
        for value in ('39.9999999999999999999', '40.01', 'NaN', 'Infinity', '-40', True, None):
            fixture = qualified_fixture()
            fixture['products'][0]['variants'][0]['price'] = value
            with self.subTest(value=value):
                self.assertFalse(gate.audit(fixture)['bundles'][0]['checks']['approved_price'])

    def test_search_node_shapes_and_full_product_shapes(self):
        fixture = qualified_fixture()
        product = fixture['products'][0]
        product['variants'] = {'edges': [{'node': v} for v in product['variants']]}
        product.pop('featuredImageUrl')
        product['featuredMedia'] = {'preview': {'image': {'url': 'https://example.test/a.png'}}}
        fixture['products'] = [{'node': p} for p in fixture['products']]
        self.assertTrue(gate.audit(fixture)['qualified_from_supplied_evidence'])

    def test_main_theme_safety_uses_role_not_development_name(self):
        fixture = qualified_fixture()
        fixture['themes'] = [{'id': 'gid://shopify/OnlineStoreTheme/1', 'name': 'Development copy', 'role': 'MAIN'},
                             {'id': '2', 'name': 'Main theme', 'role': 'UNPUBLISHED'}]
        themes = gate.audit(fixture)['themes']
        self.assertTrue(themes[0]['production_mutation_prohibited'])
        self.assertFalse(themes[1]['production_mutation_prohibited'])

    def test_detroit_key_label_mismatches_are_not_audio_proof(self):
        fixture = qualified_fixture()
        fixture['products'] += [
            {'id': 'detroit1', 'title': 'Motor City Cipher — C# Minor 100 BPM'},
            {'id': 'detroit2', 'title': 'Afterhours — A# Minor 95 BPM'}]
        fixture['files'] = [{'filename': 'Motor_City_Cipher_Cmin_100_preview.mp3'},
                            {'url': 'https://example.test/Afterhours_Amin_95_preview.mp3?x=1'},
                            {'filename': 'Unrelated_Cmin_preview.mp3'}]
        report = gate.audit(fixture)
        self.assertEqual(2, len(report['metadata_findings']))
        self.assertTrue(all(not x['audio_key_verified'] for x in report['metadata_findings']))
        self.assertEqual({'C# minor', 'A# minor'}, {x['product_label'] for x in report['metadata_findings']})
        self.assertTrue(report['qualified_from_supplied_evidence'])
        self.assertTrue(report['catalog_metadata_review_required'])
        self.assertFalse(report['production_approval'])

    def test_actual_detroit_catalog_and_preview_labels_match_for_audit(self):
        fixture = qualified_fixture()
        fixture['products'] += [
            {'id': 'motor', 'title': 'Detroit-Motor City Cipher-C#min_120bpm'},
            {'id': 'after', 'title': 'Detroit-Afterhours Transit-A#min_98bpm'}]
        fixture['files'] = [
            {'filename': 'Field.001-Motor_City_Cipher_Cmin_120bpm-Omega_House_30sec_PREVIEW.mp3'},
            {'filename': 'Field.001-Afterhours_Transit_Amin_98bpm-Omega_House_30sec_PREVIEW.mp3'}]
        report = gate.audit(fixture)
        self.assertEqual(2, len(report['metadata_findings']))
        self.assertEqual({'motor', 'after'}, {x['product_id'] for x in report['metadata_findings']})
        self.assertTrue(report['qualified_from_supplied_evidence'])
        self.assertTrue(report['catalog_metadata_review_required'])
        self.assertFalse(report['production_approval'])
        self.assertEqual([], report['blockers'])
        self.assertTrue(all(not bundle['metadata_findings'] for bundle in report['bundles']))
        self.assertTrue(all(not x['audio_key_verified'] for x in report['metadata_findings']))

    def test_literal_sharp_filename_is_preserved_and_malformed_source_safe(self):
        fixture = qualified_fixture()
        fixture['products'].append({'id': 'detroit1', 'title': 'Motor City Cipher — C# Minor 100 BPM'})
        fixture['files'] = [{'filename': 'Motor_City_Cipher_C#min_preview.mp3'}, {'originalSource': 'malformed'}]
        self.assertEqual([], gate.audit(fixture)['metadata_findings'])

    def test_metadata_defect_blocks_only_affected_bundle(self):
        fixture = qualified_fixture()
        product = fixture['products'][0]
        product['title'] = 'Test Collection — C# Minor'
        fixture['files'] = [{'product_id': product['id'], 'filename': 'Test_Collection_Cmin_preview.mp3'}]
        report = gate.audit(fixture)
        self.assertFalse(report['bundles'][0]['qualified_from_supplied_evidence'])
        self.assertIn('metadata_label_mismatch', report['bundles'][0]['blockers'])
        self.assertTrue(report['bundles'][1]['qualified_from_supplied_evidence'])
        self.assertEqual([], report['bundles'][1]['metadata_findings'])
        self.assertTrue(report['catalog_metadata_review_required'])
        self.assertFalse(report['production_approval'])

    def test_no_invented_fulfillment_or_prose_based_license(self):
        fixture = qualified_fixture()
        fixture['products'][0]['description'] = 'Delivery verified, royalty free, checkout tested.'
        supplied = fixture['verified_delivery']['15471014510828']
        supplied['delivery'] = 'verified'
        supplied['license'] = {'passed': True}
        del supplied['checkout']
        checks = gate.audit(fixture)['bundles'][0]['checks']
        self.assertFalse(checks['delivery'])
        self.assertFalse(checks['license'])
        self.assertFalse(checks['checkout'])

    def test_evidence_must_be_bound_to_product_and_timestamp(self):
        fixture = qualified_fixture()
        supplied = fixture['verified_delivery']['15471014510828']
        supplied['delivery']['subject_product_id'] = 'different'
        supplied['license']['observed_at'] = '2026-99-25T00:00:00Z'
        supplied['checkout']['sha256'] = 'not-a-hash'
        self.assertFalse(gate.audit(fixture)['bundles'][0]['qualified_from_supplied_evidence'])

    def test_component_manifest_exact_and_adlib_identity_required(self):
        fixture = qualified_fixture()
        supplied = fixture['verified_delivery']['15471014543596']
        supplied['components'] = supplied['components'] + ['extra_unapproved_component']
        supplied.pop('adlib93_asset_kind')
        report = gate.audit(fixture)['bundles'][1]
        self.assertIn('component_manifest_missing_or_mismatch', report['blockers'])
        self.assertIn('adlib93_asset_identity_unresolved', report['blockers'])

    def test_binary_requires_all_six_plugin_gates(self):
        fixture = qualified_fixture()
        supplied = fixture['verified_delivery']['15471014543596']
        supplied['adlib93_asset_kind'] = 'plugin_binary'
        result = gate.audit(fixture)['bundles'][1]
        self.assertIn('plugin_host_evidence_missing_or_invalid', result['blockers'])
        for key in ('build', 'dsp', 'state', 'host', 'cpu', 'design'):
            supplied['plugin_' + key] = evidence('15471014543596')
        self.assertTrue(gate.audit(fixture)['bundles'][1]['qualified_from_supplied_evidence'])

    def test_null_media_and_missing_sku_fail_closed(self):
        fixture = qualified_fixture()
        product = fixture['products'][0]
        product.pop('featuredImageUrl')
        product['featuredMedia'] = {'preview': {'image': None}}
        product['variants'][0].pop('sku')
        checks = gate.audit(fixture)['bundles'][0]['checks']
        self.assertFalse(checks['image_present'])
        self.assertFalse(checks['sku_present'])

    def test_deterministic_report_does_not_mutate_input(self):
        fixture = qualified_fixture()
        original = copy.deepcopy(fixture)
        self.assertEqual(gate.audit(fixture), gate.audit(fixture))
        self.assertEqual(fixture, original)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.json'
            path.write_text('{}')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, gate.main([str(path)]))
                self.assertEqual(2, gate.main([str(path), '--require-qualified']))
                path.write_text('{')
                self.assertEqual(1, gate.main([str(path)]))


if __name__ == '__main__':
    unittest.main()
