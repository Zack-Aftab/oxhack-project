import datetime as dt
import importlib.util
from pathlib import Path
from unittest import TestCase,main
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('m',Path(__file__).resolve().parents[1]/'specialists.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class SpecialistTests(TestCase):
 def test_every_category_combination_has_a_hub_and_only_complete_matches(self):
  import itertools
  cats=[c for c in m.MAPPING if c!='unknown']
  for n in range(1,len(cats)+1):
   for combo in itertools.combinations(cats,n):
    self.assertIn('H001',m.eligible(combo))
    for h in m.eligible(combo):self.assertTrue(set(m.required(combo))<=m.COVERAGE[h])
 def test_unknown_requires_self_selection(self):
  for cats in [[],['unknown'],['unknown','cuts_or_wounds'],['invented']]:
   with self.assertRaises(ValueError):m.eligible(cats)
 def test_orthopaedic_need_excludes_sites_without_it(self):
  self.assertEqual(m.eligible(['fracture_sprain_or_dislocation']),['H001','H002','H005'])
  self.assertEqual(m.eligible(['fracture_sprain_or_dislocation','chest_pain_or_heart_symptoms']),['H001'])
 def test_float_urgency_prioritises_nonbed_patients_without_interrupting_care(self):
  start=dt.datetime(2026,9,21,tzinfo=m.ZONE);end=start+dt.timedelta(days=1)
  def patient(name,minute,score):return {'visit_id':name,'hospital_id':'H001','arrival_at':m.iso(start.timestamp()+minute*60),'complaint_categories':['other_or_uncategorised'],'required_specialties':['emergency_medicine'],'urgency_rating':score,'likely_bed_occupancy':False,'is_emergency':False,'is_warmup':False}
  patients=[patient('A',0,5.5),patient('B',1,2.2),patient('C',2,8.7)]
  profiles={'H001':{'general_doctors_by_four_hour_block':[1]*6,'triage_nurses_by_four_hour_block':[2]*6,'support_beds':1,'specialist_doctors_on_duty':{s:0 for s in m.SPECIALTIES}}}
  with patch.object(m,'duration',side_effect=lambda r,mean,cv=.6:mean*60):
   waits,_,_=m.simulate(patients,start,end,1,1,20/m.WEIGHTS['other_or_uncategorised'],profiles)
  self.assertEqual(waits['C'],22.5);self.assertEqual(waits['B'],43.5)
 def test_waiting_time_allowance_prevents_starvation_without_overtaking_bed_priority(self):
  base=dt.datetime(2026,9,21,tzinfo=m.ZONE).timestamp()
  old={'visit_id':'old','arrival_at':m.iso(base),'urgency_rating':2.0,'likely_bed_occupancy':False}
  new={'visit_id':'new','arrival_at':m.iso(base+200*60),'urgency_rating':8.0,'likely_bed_occupancy':False}
  bed={'visit_id':'bed','arrival_at':m.iso(base+200*60),'urgency_rating':10.0,'likely_bed_occupancy':True}
  self.assertLess(m.queue_priority(old),m.queue_priority(new))
  self.assertLess(m.queue_priority(new,0),m.queue_priority(old,0))
  self.assertLess(m.queue_priority(bed),m.queue_priority(old))
 def test_emergency_exit_never_waits_for_manual_category_selection(self):
  v={'visit_id':'e','arrival_at':'2026-09-21T00:00:00+01:00','is_emergency':True,'manual_category_confirmation':True,'complaint_categories':['unknown'],'required_specialties':[]}
  result=m.output_patient(v,[])
  self.assertEqual(result['complaint_categories'],[])
  self.assertFalse(result['manual_category_confirmation'])
  self.assertIsNone(result['mean_wait_to_first_doctor_minutes'])
 def test_profile_plan_has_explicit_boolean_support_and_positive_supported_specialist_counts(self):
  import json
  source=json.loads((Path(__file__).resolve().parents[1]/'input.json').read_text())
  *_,profiles=m.plan(source)
  for h,p in profiles.items():
   self.assertEqual(set(p['support']),set(m.SPECIALTIES))
   for specialty,value in p['support'].items():
    self.assertIs(type(value),bool)
    if specialty!='emergency_medicine':self.assertEqual(p['specialist_doctors_on_duty'][specialty]>0,value)
  self.assertEqual(len({tuple(sorted(m.COVERAGE[h])) for h in profiles}),5)

if __name__=='__main__':main()
