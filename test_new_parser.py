#!/usr/bin/env python3

from app.parser import parse_lab_tests

# Test with multiple different lab report formats
test_cases = [
    {
        "name": "Multi-line format (original)",
        "text": """
kauvery
1pd.
UHID/IP
IPHS00059614(IP)
Patient
BedNo:Ward
102-3/MCU
Dr. Raghunath R. MBBS , MD
Report Date
08 12 PM
Order No
. 6245678 - Final
ELECTROLYTES ALL
Sodium
131
mmoliL
132-146
Mne:F.FAh
Potassium
5.6
mmol L
5-5
VrLFm
Chlorde
102
mmcl'l
9P-107
MenC.PerA
Sample Collected Detals
Serur 70:20.
od Glucose Random (RBS)
94
mg/dL
70-140
Sample Collected Details
ANNIE ROSE L. MBBS .DNB (CONSULTANT
Sibiya
PATHOLOGIST)
Validated By
Reg No.KMC 102865
Approved By
SEROLOGY
Investigatlon
C Reactive
>90.0
mgL
05
Men.nede utm
Sample Collected Detals
Sem
ANNIE ROSE L. MBBS DNB(CONSULTANT
Sibiya
PATHOLOGIST
Reg No KMC 102865
Validated By
Approved By
Page 21
"""
    },
    {
        "name": "Single-line format",
        "text": """
LABORATORY REPORT
Patient: John Doe
Date: 2024-01-15

Sodium 140 mmol/L 135-145
Potassium 4.2 mmol/L 3.5-5.0
Chloride 102 mmol/L 96-107
Glucose 95 mg/dL 70-140
Creatinine 1.2 mg/dL 0.7-1.3
"""
    },
    {
        "name": "Mixed format",
        "text": """
COMPREHENSIVE METABOLIC PANEL
Date: 2024-01-15

Sodium: 142 mmol/L (135-145)
Potassium: 4.1 mmol/L (3.5-5.0)
Chloride: 104 mmol/L (96-107)
CO2: 24 mmol/L (22-28)
Glucose: 92 mg/dL (70-140)
BUN: 15 mg/dL (7-20)
Creatinine: 1.1 mg/dL (0.7-1.3)
Calcium: 9.8 mg/dL (8.5-10.5)
"""
    },
    {
        "name": "Compact format",
        "text": """
CBC Results:
WBC 7.2 K/uL 4.0-11.0
RBC 4.8 M/uL 4.2-5.8
HGB 14.2 g/dL 12.0-16.0
HCT 42% 37-47
MCV 88 fL 80-100
MCH 30 pg 27-33
MCHC 34 g/dL 32-36
PLT 250 K/uL 150-450
"""
    },
    {
        "name": "Noisy multi-line OCR (user sample)",
        "text": """
RSteI
MIMS
HOSPITAI
th
Ihumbetholih.
( :r\BR\IH
\PII
16.9
(l
31.01
Date-
( BC(OMPI.I.I RIOOD)COLN)
Haemoglobin Fstimation 15.3
4.9
hul
lotallehoteouut
二（
10
hul
2.
Platelet(out
5.11
41.1
RB((outRl Blol
(vll)
P(VHacmatorin
44.5
Men Corpuscull.r
83.4
11
VolumeM
28.
Mean corpenlar
2.
hemoglobinMH
34.4
Me:n corpeulr
hemnglobn
ntatjon MH
14.9
Red cell dtriburion
Wdh-(\"(RDW)
15.
Platekt distributio
5.141
WdthPDM
Ve.n platelet
8.
1.
volume(MPV,
Dillerenil uo te cnD
2-1
Veunophils
"""
    },
    {
        "name": "Real OCR output (user sample)",
        "text": """|} 725 PSGAR SUPER: SPECIALITY HOSPITAL 2s.
(2) Pore enn agneae AG
«| {i Opp..Givil' Hospital, Sonipat:|:Mobs7> OE
Patiepr Name, si iMRS.POOIA {| Bate
«Hl! SERUM BILIRUBIN Ce a |i
| INDIRECT BILIRUBIN"""
    }
]

if __name__ == "__main__":
    print("Testing flexible parser with multiple formats...")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 40)
        
        results = parse_lab_tests(test_case['text'])
        
        print(f"Found {len(results)} lab test results:")
        
        if results:
            for j, result in enumerate(results, 1):
                print(f"  {j}. {result['test_name']}")
                print(f"     Value: {result['value']} {result['unit'] or ''}")
                print(f"     Range: {result['ref_range'] or 'N/A'}")
                print(f"     Flag: {result['flag'] or 'Normal'}")
        else:
            print("  No results found")
        
        print() 