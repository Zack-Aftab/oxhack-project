import copy
import datetime as dt
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import specialists as m

class HourlyCapacityTests(TestCase):
 def run_queue(self,hourly=None):
  start=dt.datetime(2026,9,21,tzinfo=m.ZONE);end=start+dt.timedelta(days=1)
  def visit(name,minute):return {'visit_id':name,'hospital_id':'H001','arrival_at':m.iso(start.timestamp()+minute*60),'complaint_categories':['other_or_uncategorised'],'required_specialties':['emergency_medicine'],'urgency_rating':3.,'likely_bed_occupancy':False,'is_emergency':False,'is_warmup':False}
  p={'general_doctors_by_four_hour_block':[1]*6,'triage_nurses_by_four_hour_block':[2]*6,'support_beds':2,'specialist_doctors_on_duty':{s:0 for s in m.SPECIALTIES}}
  if hourly is not None:p['general_doctors_by_hour']=hourly
  with patch.object(m,'duration',side_effect=lambda r,mean,cv=.6:mean*60):return m.simulate([visit('A',50),visit('B',51)],start,end,1,1,50/m.WEIGHTS['other_or_uncategorised'],{'H001':p})
 def test_extra_hourly_doctor_starts_waiting_patient_without_preempting_current_consultation(self):
  roster=[1]*24;roster[1]=2
  waits,_,_=self.run_queue(roster)
  self.assertEqual(waits['A'],4.5)
  self.assertEqual(waits['B'],9.)
  baseline,_,_=self.run_queue()
  self.assertEqual(baseline['B'],53.5)
 def test_unchanged_hourly_and_four_hour_counts_produce_identical_waits(self):
  coarse,coarse_areas,_=self.run_queue();hourly,hourly_areas,_=self.run_queue([1]*24)
  self.assertEqual(coarse,hourly)
  self.assertEqual(coarse_areas['H001']['general_capacity_seconds'],hourly_areas['H001']['general_capacity_seconds'])
 def test_incomplete_or_invalid_hourly_staffing_is_rejected(self):
  for roster in [[1]*23,[1]*23+[0],[1]*23+[True]]:
   with self.assertRaisesRegex(ValueError,'24 positive integer'):self.run_queue(roster)
