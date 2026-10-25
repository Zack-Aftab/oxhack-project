import gzip,json,math,sys
from pathlib import Path
from unittest import TestCase
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import fit_demo_distribution as f

class FittedDistributionTests(TestCase):
 @classmethod
 def setUpClass(cls):
  cls.model=json.loads(gzip.decompress((root/'results/fitted-v11/model.json.gz').read_bytes()))
  cls.data=json.loads(gzip.decompress((root/'results/fitted-v11/dataset.json.gz').read_bytes()))
  cls.source=json.loads(gzip.decompress((root/'results/distribution-v10/dataset.json.gz').read_bytes()))
 def test_every_fitted_record_matches_frozen_model_and_preserves_raw_queue_and_patient(self):
  self.assertEqual(len(self.source['visits']),len(self.data['visits']))
  for before,after in zip(self.source['visits'],self.data['visits']):
   for k in ['visit_id','hospital_id','arrival_at','complaint_categories','pain_score','urgency_rating','likely_bed_occupancy','is_emergency']:self.assertEqual(before[k],after[k])
   if after['is_emergency']:
    self.assertIsNone(after['fitted_demo_wait_minutes']);self.assertIsNone(after['estimated_wait_to_first_doctor_minutes'])
   else:
    raw=before['simulation_waits_minutes'][0]
    self.assertEqual(after['raw_queue_wait_minutes'],raw)
    self.assertEqual(after['fitted_demo_wait_minutes'],f.apply_fitted_wait(raw,self.model))
    self.assertEqual(after['estimated_wait_to_first_doctor_minutes'],math.ceil(after['fitted_demo_wait_minutes']))
 def test_target_distribution_mean_and_median_are_actually_met(self):
  waits=[v['fitted_demo_wait_minutes'] for v in self.data['visits'] if not v['is_emergency']]
  bins=f.m.bins(waits)
  for actual,target in zip(bins,self.model['target_percentages']):self.assertAlmostEqual(actual['percent'],target,delta=.002)
  self.assertAlmostEqual(f.statistics.mean(waits),120,places=6)
  self.assertEqual(f.statistics.median(waits),100)
 def test_frozen_mapping_preserves_order_for_capacity_comparisons_and_refuses_extreme_unfitted_values(self):
  source=self.model['source_queue_waits_sorted'];sample=source[::1000]
  fitted=[f.apply_fitted_wait(x,self.model) for x in sample]
  self.assertEqual(fitted,sorted(fitted))
  with self.assertRaisesRegex(ValueError,'exceeds calibration support'):f.apply_fitted_wait(source[-1]+1,self.model)
  for invalid in [float('nan'),float('inf'),-1]:
   with self.assertRaises(ValueError):f.apply_fitted_wait(invalid,self.model)
