import type { Metadata } from "next";
import { HospitalShell } from "@/components/hospital/HospitalShell";

export const metadata: Metadata = { title: "Hospital · operations demo" };

export default function HospitalPage() {
  return <HospitalShell />;
}
