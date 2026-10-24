import datetime as dt
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('resource_model', Path(__file__).resolve().parents[1]/'engine.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
BASE = m.ts('2026-09-21T00:00:00+01:00')


def patient(name, minute, flag=False, review=False):
    return {'visit_id': name, 'hospital_id': 'H1', 'arrival_at': m.iso(BASE+minute*60),
            'complaint_category': 'cuts_or_wounds', 'required_specialty_for_demo_model': 'wound_care_or_plastics',
            'likely_bed_occupancy': flag, 'requires_specialist_review': review, 'is_warmup':False}


def schedule(doctors=1, beds=2, specialists=1):
    return [{'snapshot_id':'s1','hospital_id':'H1','snapshot_at':m.iso(BASE),
             'general_doctors_available':doctors,'triage_nurses_available':2,'beds_available':beds,
             'specialty_doctors_available':{'wound_care_or_plastics':specialists}},
            {'snapshot_id':'s2','hospital_id':'H1','snapshot_at':m.iso(BASE+3600),
             'general_doctors_available':doctors,'triage_nurses_available':2,'beds_available':beds,
             'specialty_doctors_available':{'wound_care_or_plastics':specialists}}]


def work(general=600, triage=0, specialist=0, response=0, bed_hold=0):
    return dict(general=general,triage=triage,specialist=specialist,response=response,bed_hold=bed_hold)


class ResourceTests(unittest.TestCase):
    def run_model(self, patients, staffing, durations, start=BASE, end=BASE+3600):
        return m.run_hospital(patients,staffing,durations,start,end)

    def test_contact_cannot_precede_triage(self):
        result,_,_,_=self.run_model([patient('A',0)],schedule(),{'A':work(triage=300)})
        self.assertEqual(result['A']['wait_minutes'],5)
        self.assertEqual(result['A']['triage_elapsed_minutes'],5)

    def test_priority_only_after_triage_no_interruption(self):
        p=[patient('A',0),patient('B',1),patient('C',2,True)]
        result,_,_,_=self.run_model(p,schedule(),{'A':work(),'B':work(),'C':work(triage=300)})
        self.assertEqual([result[k]['wait_minutes'] for k in ('A','B','C')],[0,19,8])

    def test_spaces_remain_occupied_during_investigations(self):
        p=[patient('A',0,True),patient('B',1,True)]
        result,_,_,_=self.run_model(p,schedule(doctors=2,beds=1),{k:work(general=60,bed_hold=1800) for k in ('A','B')})
        self.assertEqual(result['B']['wait_minutes'],29)

    def test_specialist_access_limits_release_and_first_contact_indirectly(self):
        p=[patient('A',0,True,True),patient('B',0,True,True),patient('C',1,True,True),patient('D',1,True,True)]
        w={v['visit_id']:work(general=60,specialist=600) for v in p}
        slow,_,_,_=self.run_model(p,schedule(doctors=4,beds=2,specialists=1),w)
        fast,_,_,_=self.run_model(p,schedule(doctors=4,beds=2,specialists=2),w)
        self.assertEqual(slow['D']['wait_minutes'],20)
        self.assertEqual(fast['D']['wait_minutes'],10)

    def test_more_doctors_reduce_same_patient_workload_wait(self):
        p=[patient('A',0),patient('B',0)];w={v['visit_id']:work() for v in p}
        one,_,_,_=self.run_model(p,schedule(doctors=1),w)
        two,_,_,_=self.run_model(p,schedule(doctors=2),w)
        self.assertEqual(one['B']['wait_minutes'],10)
        self.assertEqual(two['B']['wait_minutes'],0)

    def test_warmup_excluded_but_ongoing_work_contributes_to_measured_utilisation(self):
        p=patient('A',0);p['is_warmup']=True
        result,_,totals,_=self.run_model([p],schedule(),{'A':work(general=900)},start=BASE+600,end=BASE+1200)
        self.assertEqual(result,{})
        self.assertEqual(totals['doctor_busy_seconds'],300)
        self.assertEqual(totals['doctor_capacity_seconds'],600)

    def test_impossible_capacity_does_not_produce_fake_finite_wait(self):
        with self.assertRaisesRegex(ValueError,'required resource'):
            self.run_model([patient('A',0,True)],schedule(beds=0),{'A':work()})

    def test_service_draws_repeat_with_same_seed_and_change_by_run(self):
        p=[patient('A',0)];config={'general_mean_minutes':{'cuts_or_wounds':20}}
        self.assertEqual(m.draw_work(p,config,5,1),m.draw_work(p,config,5,1))
        self.assertNotEqual(m.draw_work(p,config,5,1),m.draw_work(p,config,5,2))

    def test_capacity_change_does_not_interrupt_ongoing_work(self):
        p=[patient('A',0),patient('B',0),patient('C',6)]
        staffing=schedule(doctors=2);staffing[1]['snapshot_at']=m.iso(BASE+300);staffing[1]['general_doctors_available']=1
        result,_,_,_=self.run_model(p,staffing,{v['visit_id']:work() for v in p})
        self.assertEqual(result['C']['wait_minutes'],4)

if __name__=='__main__':
    unittest.main()
