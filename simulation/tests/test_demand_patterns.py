import datetime as dt
import gzip
import importlib.util
import json
from pathlib import Path
import sys
from unittest import TestCase
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import demand_patterns as d

class DemandPatternTests(TestCase):
 def test_total_expected_demand_is_450_per_site_per_day_across_measured_month(self):
  self.assertAlmostEqual(sum(d.ORIGIN_FACTORS.values()),5)
  total=sum(450*f*d.m.WEEKDAY[(d.START+dt.timedelta(days=i)).weekday()]/d.WEEKDAY_NORM for f in d.ORIGIN_FACTORS.values() for i in range(30))
  self.assertAlmostEqual(total,450*5*30)
 def test_commute_and_weekend_patterns_change_relative_case_mix(self):
  raw={'fracture_sprain_or_dislocation':1,'abdominal_or_stomach_problems':1,'other_or_uncategorised':1,'cuts_or_wounds':1,'head_injury_or_neurological_symptoms':1}
  self.assertGreater(d.case_weights(raw,0,2)['fracture_sprain_or_dislocation'],d.case_weights(raw,6,2)['fracture_sprain_or_dislocation'])
  self.assertGreater(d.case_weights(raw,5,2)['abdominal_or_stomach_problems'],d.case_weights(raw,0,2)['abdominal_or_stomach_problems'])
 def test_one_run_output_has_complete_matched_coverage_and_integer_ceiling(self):
  file=root/'results/demand-v8/dataset.json.gz'
  self.assertTrue(file.exists(),'Committed run artifact required')
  data=json.loads(gzip.decompress(file.read_bytes()))
  self.assertEqual(data['dataset_metadata']['runs'],1)
  for v in data['visits']:
   if v['is_emergency']:
    self.assertIsNone(v['hospital_id']);self.assertEqual(v['simulation_waits_minutes'],[])
   else:
    self.assertIn(v['hospital_id'],d.m.eligible(v['complaint_categories']))
    self.assertEqual(len(v['simulation_waits_minutes']),1)
    self.assertEqual(v['mean_wait_to_first_doctor_minutes'],d.math.ceil(v['simulation_waits_minutes'][0]))
    if v['likely_bed_occupancy']:
     self.assertEqual(v['urgency_rating'],10);self.assertEqual(v['queue_priority_tier'],15)
    else:self.assertLessEqual(v['urgency_rating'],7.5)
