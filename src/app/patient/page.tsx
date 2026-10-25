import type { Metadata } from "next";
import { PatientShell } from "@/components/patient/PatientShell";

export const metadata: Metadata = { title: "Patient · hospital comparison demo" };

export default function PatientPage() {
  return <PatientShell />;
}
