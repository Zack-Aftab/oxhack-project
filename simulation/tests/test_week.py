import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('week',Path(__file__).resolve().parents[1]/'run.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
m=w.m
BASE=m.ts('2026-09-21T00:00:00+01:00')

class WeekTests(unittest.TestCase):
    def test_known_flag_prioritises_triage_without_interrupting_ongoing_triage(self):
        def patient(name,minute,flag):
            return {'visit_id':name,'hospital_id':'H1','arrival_at':m.iso(BASE+minute*60),'likely_bed_occupancy':flag,
                    'requires_specialist_review':False,'is_warmup':False}
        patients=[patient('A',0,False),patient('B',1,False),patient('C',2,True)]
        schedule=[{'snapshot_id':'s','hospital_id':'H1','snapshot_at':m.iso(BASE),'general_doctors_available':3,
                   'triage_nurses_available':1,'beds_available':2,'specialty_doctors_available':{}}]
        work={v['visit_id']:{'triage':600,'general':60,'response':0,'specialist':0,'bed_hold':0} for v in patients}
        result,_,_,_=m.run_hospital(patients,schedule,work,BASE,BASE+3600,triage_priority=True)
        self.assertEqual(result['A']['triage_elapsed_minutes'],10)
        self.assertEqual(result['C']['triage_elapsed_minutes'],18)
        self.assertEqual(result['B']['triage_elapsed_minutes'],29)
        # All patients get a full general-doctor encounter before departure.
        for v in patients:
            r=result[v['visit_id']]
            self.assertEqual(r['departure_at']-m.ts(v['arrival_at'])-r['wait_minutes']*60,60)

    def test_known_flag_prioritises_general_doctor_after_triage(self):
        patients=[{'visit_id':name,'hospital_id':'H1','arrival_at':m.iso(BASE+at*60),'likely_bed_occupancy':flag,
                   'requires_specialist_review':False,'is_warmup':False} for name,at,flag in [('A',0,False),('B',1,False),('C',2,True)]]
        schedule=[{'snapshot_id':'s','hospital_id':'H1','snapshot_at':m.iso(BASE),'general_doctors_available':1,
                   'triage_nurses_available':2,'beds_available':2,'specialty_doctors_available':{}}]
        work={v['visit_id']:{'triage':0,'general':600,'response':0,'specialist':0,'bed_hold':0} for v in patients}
        result,_,_,_=m.run_hospital(patients,schedule,work,BASE,BASE+3600,triage_priority=True)
        self.assertEqual(result['C']['wait_minutes'],8)
        self.assertEqual(result['B']['wait_minutes'],19)

    def test_report_bins_include_boundaries_and_cover_every_observation(self):
        values=[0,10,10.1,24,24.1,60,60.1,120,120.1,240,240.1]
        rows=w.waiting_bins(values)
        self.assertEqual([r['count'] for r in rows],[2,2,2,2,2,1])
        self.assertEqual(sum(r['count'] for r in rows),len(values))
        self.assertAlmostEqual(sum(r['percent'] for r in rows),100)

    def test_empty_system_can_have_fast_contacts_no_artificial_wait_floor(self):
        patients=[{'visit_id':'A','hospital_id':'H1','arrival_at':m.iso(BASE),'likely_bed_occupancy':False,
                   'requires_specialist_review':False,'is_warmup':False}]
        schedule=[{'snapshot_id':'s','hospital_id':'H1','snapshot_at':m.iso(BASE),'general_doctors_available':1,
                   'triage_nurses_available':1,'beds_available':2,'specialty_doctors_available':{}}]
        work={'A':{'triage':60,'general':600,'response':0,'specialist':0,'bed_hold':0}}
        result,_,_,_=m.run_hospital(patients,schedule,work,BASE,BASE+3600,triage_priority=True)
        self.assertEqual(result['A']['wait_minutes'],1)

if __name__=='__main__':unittest.main()
