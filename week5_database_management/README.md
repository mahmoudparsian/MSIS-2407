# Week 5 — Database Administration and Management

[← Week 4](../week4_data_warehousing/README.md) · [Course home](../README.md) · **Week 5 of 5**

A database that works is not finished — it has to stay secure, recoverable,
and trustworthy. This week takes the database administrator's view: who may
see the data, and what happens when something goes wrong.

**Topics:** the DBA role: performance and monitoring · security and access
control (views, PII, SQL injection) · backup, recovery (RPO / RTO), and
capacity · data quality and governance

## At a Glance

| Session | Lab topic | Lab folder |
|:---:|---|---|
| **9** | Security, access control, indexes, auditing | `LABS/week5_lab1/` |
| **10** | Backup, recovery, and data quality | `LABS/week5_lab2/` |

---

## Slides

[`week5_lecture_slides.pdf`](week5_lecture_slides.pdf) — the week's deck
(source: [`week5_lecture_slides.md`](week5_lecture_slides.md)). Its last slide
previews the Final Exam.

## Lecture Notes

| Session | Notes | What they cover |
|:---:|---|---|
| **9** | [Security and Access Control](lecture_notes_01_Security_and_Access_Control.md) | The three questions of database security; role-based access control and least privilege; views as a security boundary; protecting PII; why removing names is not anonymization; k-anonymity; SQL injection |
| **10** | [Backup, Recovery, Capacity, and Governance](lecture_notes_02_Recovery_and_Governance.md) | Why an untested backup is only a hypothesis; RPO and RTO; backup types; capacity planning; the dimensions of data quality; reversible remediation; catalogs and lineage; monitoring and the runbook |

This week has no demo notebook — the labs are where you practice.

---

## Labs

Each session's labs are published in [`LABS/`](../LABS/) during class — an
**a** lab (core) and a **b** lab (a step more challenging); the instructor
announces which count. Solutions are added after the 11:00 pm deadline.

## Final Exam

The Final Exam (300 points) covers the whole course and is held in a separate
exam slot after Session 10. Its format is described in
[`ASSIGNMENTS_and_GRADING.md`](../course_information/ASSIGNMENTS_and_GRADING.md).
Install the lock-down browser at least a week before the exam — see
[`software_installation/`](../software_installation/README.md) (Step 5).

---

[← Week 4](../week4_data_warehousing/README.md) · [Course home](../README.md)
