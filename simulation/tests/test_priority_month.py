import datetime as dt
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('priority_model',Path(__file__).resolve().parents[1]/'archive/priority_v3.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
m=p.model
BASE=m.ts('2026-09-21T00:00:00+01:00')

class PriorityTests(unittest.TestCase):
    def test_urgency_varies_by_time_and_category_but_expected_rate_is_three_percent(self):
        cohort=[]
        for day in range(7):
            for hour in range(24):
                for category in p.URGENCY_CATEGORY:
                    arrival=dt.datetime(2026,9,21,tzinfo=m.ZONE)+dt.timedelta(days=day,hours=hour)
                    cohort.append({'visit_id':f'{day}-{hour}-{category}','arrival_at':arrival.isoformat(),
                                   'complaint_category':category,'is_warmup':False,'likely_bed_occupancy':False})
        labelled=p.assign_urgency(cohort,7)
        self.assertAlmostEqual(sum(v['synthetic_urgency_probability'] for v in labelled)/len(labelled),.03)
        self.assertGreater(len({v['synthetic_urgency_probability'] for v in labelled}),1)
        self.assertEqual(labelled,p.assign_urgency(cohort,7))
        for original,new in zip(cohort,labelled):
            for key,value in original.items():self.assertEqual(new[key],value)
            self.assertIs(type(new['clinician_urgent']),bool)
        self.assertTrue(any(v['clinician_urgent'] and not v['likely_bed_occupancy'] for v in labelled))

    def test_clinical_priority_is_independent_of_bed_flag(self):
        def visit(name,minute,bed,urgent):
            return {'visit_id':name,'arrival_at':m.iso(BASE+minute*60),'hospital_id':'H1','likely_bed_occupancy':bed,
                    'clinician_urgent':urgent,'requires_specialist_review':False,'is_warmup':False}
        patients=[visit('A',0,False,False),visit('B',1,True,False),visit('C',2,False,True)]
        schedule=[{'snapshot_id':'s','hospital_id':'H1','snapshot_at':m.iso(BASE),'general_doctors_available':1,
                   'triage_nurses_available':2,'beds_available':2,'specialty_doctors_available':{} }]
        work={v['visit_id']:{'triage':0,'general':600,'specialist':0,'response':0,'bed_hold':0} for v in patients}
        result,_,_,_=m.run_hospital(patients,schedule,work,BASE,BASE+3600,priority_field='clinician_urgent')
        self.assertEqual(result['C']['wait_minutes'],8)
        self.assertEqual(result['B']['wait_minutes'],19)

if __name__=='__main__':unittest.main()
