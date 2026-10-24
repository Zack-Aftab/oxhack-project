import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('simulation', Path(__file__).resolve().parents[1]/'archive/month_v1.py')
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)


def visit(id, at, bed=False, specialty='emergency_medicine'):
    return {'visit_id': id, 'hospital_id': 'H1', 'arrival_at': f'2026-09-21T00:{at:02}:00+01:00', 'complaint_category': 'cuts_or_wounds', 'likely_bed_occupancy': bed, 'required_specialty_for_demo_model': specialty}


def snapshot(doctors=1, beds=2, specialists=1):
    return {'snapshot_id': 'S1', 'hospital_id': 'H1', 'snapshot_at': '2026-09-21T00:00:00+01:00', 'general_doctors_available': doctors, 'beds_available': beds, 'specialty_doctors_available': {'orthopaedics': specialists}}


class SimulationTests(unittest.TestCase):
    def test_priority_overtakes_waiting_patient_but_does_not_interrupt_work(self):
        patients = [visit('A', 0), visit('B', 1), visit('C', 2, True)]
        r = sim.simulate(patients, [snapshot()], {v['visit_id']: (600, 0) for v in patients})
        self.assertEqual(r['waits'], {'A': 0, 'B': 19, 'C': 8})

    def test_more_doctors_reduce_wait_for_identical_work(self):
        patients = [visit('A', 0), visit('B', 0)]
        work = {'A': (600, 0), 'B': (600, 0)}
        one = sim.simulate(patients, [snapshot(doctors=1)], work)
        two = sim.simulate(patients, [snapshot(doctors=2)], work)
        self.assertEqual(sum(one['waits'].values()), 10)
        self.assertEqual(sum(two['waits'].values()), 0)

    def test_bed_is_held_until_specialist_work_completes(self):
        patients = [visit('A', 0, True, 'orthopaedics'), visit('B', 1, True, 'orthopaedics')]
        work = {'A': (600, 1200), 'B': (600, 1200)}
        r = sim.simulate(patients, [snapshot(doctors=2, beds=1)], work)
        self.assertEqual(r['waits']['B'], 29)
        r = sim.simulate(patients, [snapshot(doctors=2, beds=2)], work)
        self.assertEqual(r['waits']['B'], 0)

    def test_specialists_affect_wait_indirectly_through_occupied_spaces(self):
        patients = [visit('A', 0, True, 'orthopaedics'), visit('B', 0, True, 'orthopaedics'), visit('C', 1, True, 'orthopaedics'), visit('D', 1, True, 'orthopaedics')]
        work = {v['visit_id']: (60, 600) for v in patients}
        slow = sim.simulate(patients, [snapshot(doctors=3, beds=2, specialists=1)], work)
        fast = sim.simulate(patients, [snapshot(doctors=3, beds=2, specialists=2)], work)
        # First free bed occurs at minute 11 in both; downstream completion differs.
        self.assertLess(fast['completed_at']['C'], slow['completed_at']['C'])
        self.assertEqual(slow['waits']['C'], 10)
        self.assertEqual(slow['waits']['D'], 20)
        self.assertEqual(fast['waits']['D'], 10)

    def test_no_finite_result_when_required_capacity_never_exists(self):
        with self.assertRaisesRegex(ValueError, 'cannot clear'):
            sim.simulate([visit('A', 0, True)], [snapshot(beds=0)], {'A': (60, 0)})

    def test_average_is_ceiled_once_after_averaging_and_stored_as_integer(self):
        for values, expected in [([0]*5, 0), ([23.1]*5, 24), ([24.0]*5, 24), ([0.1, 0.1, 0.1, 0.1, 4.6], 1)]:
            result = sim.aggregate_patient(visit('A', 0), values)
            self.assertEqual(result['mean_wait_to_first_doctor_minutes'], expected)
            self.assertIs(type(result['mean_wait_to_first_doctor_minutes']), int)
            elapsed = sim.timestamp(result['mean_first_doctor_at']) - sim.timestamp(result['arrival_at'])
            self.assertEqual(elapsed, expected * 60)
            self.assertEqual(result['simulation_waits_minutes'], values)

    def test_fixed_labels_and_work_draws_are_reproducible(self):
        patients = [visit('A', 0), visit('B', 1)]
        self.assertEqual(sim.label_patients(patients, 5), sim.label_patients(patients, 5))
        self.assertEqual(sim.durations(patients, 5, 1), sim.durations(patients, 5, 1))
        self.assertNotEqual(sim.durations(patients, 5, 1), sim.durations(patients, 5, 2))

if __name__ == '__main__':
    unittest.main()
