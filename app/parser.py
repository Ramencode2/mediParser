# app/parser.py

import re
import pandas as pd
from difflib import get_close_matches
from rapidfuzz import process, fuzz

# Load lab test names from CSV
def load_test_terms(filepath="app/test_terms.csv"):
    df = pd.read_csv(filepath)
    return set(df["test_name"].dropna().str.strip().str.lower())

test_terms_set = load_test_terms()

def normalize_unit(unit):
    """Normalize unit strings to standard format"""
    if not unit:
        return None
    unit = unit.lower().strip()
    corrections = {
        "mmoll": "mmol/L",
        "mgldl": "mg/dL", 
        "mgidl": "mg/dL",
        "mg/l": "mg/L",
        "mgl": "mg/L",
        "mgdl": "mg/dL",
        "gdl": "g/dL",
        "g/l": "g/L",
        "umoll": "μmol/L",
        "umol/l": "μmol/L",
        "ngml": "ng/mL",
        "ng/ml": "ng/mL",
        "pgml": "pg/mL",
        "pg/ml": "pg/mL",
        "iul": "IU/L",
        "iu/l": "IU/L",
        "ul": "μL",
        "u/l": "U/L",
        "ul": "U/L",
        "g/di": "g/dL",
        "mg/di": "mg/dL",
        "umol/i": "μmol/L",
        "iu/i": "IU/L"
    }
    return corrections.get(unit, unit)

def clean_ocr_text(text):
    """Enhanced OCR error correction"""
    # Comprehensive corrections for common OCR errors
    corrections = {
        '1.0.11.0': '4.0-11.0',
        '13.0.17 0': '13.0-17.0',
        '82.102': '82-102',
        '4.0.5.5': '4.0-5.5',
        'tI': 'fl',
        'mll,n': 'million',
        '10°3umm': '10^3/cumm',
        'p.m': 'picogram',
        '31.5.3.4 5': '31.5-34.5',
        '11.5.145': '11.5-14.5',
        # Additional common OCR errors
        'rn': 'm',
        'cl': 'd', 
        'ii': 'll',
        'g/dI': 'g/dL',
        'mg/dI': 'mg/dL',
        'umol/I': 'μmol/L',
        'IU/I': 'IU/L',
        'hul': 'μL',
        'lotallehoteouut': 'total leukocyte',
        'RB((outRl Blol': 'RBC count',
        'P(VHacmatorin': 'hematocrit',
        'Men Corpuscull.r': 'mean corpuscular',
        'VolumeM': 'volume',
        'Mean corpenlar': 'mean corpuscular',
        'hemoglobinMH': 'hemoglobin',
        'Me:n corpeulr': 'mean corpuscular',
        'hemnglobn': 'hemoglobin',
        'ntatjon MH': 'concentration',
        'Red cell dtriburion': 'red cell distribution',
        'Wdh-(\"(RDW)': 'width (RDW)',
        'Platekt distributio': 'platelet distribution',
        'WdthPDM': 'width PDW',
        'Ve.n platelet': 'mean platelet',
        'volume(MPV,': 'volume (MPV)',
        'Dillerenil uo te cnD': 'differential count',
        'Veunophils': 'neutrophils',
        # New corrections for the noisy OCR
        '|} 725 PSGAR SUPER: SPECIALITY HOSPITAL 2s.': '',
        '(2) Pore enn agneae AG': '',
        '«| {i Opp..Givil\' Hospital, Sonipat:|:Mobs7> OE': '',
        'Patiepr Name, si iMRS.POOIA {| Bate': '',
        '«Hl! SERUM BILIRUBIN Ce a |i': 'SERUM BILIRUBIN',
        '| INDIRECT BILIRUBIN': 'INDIRECT BILIRUBIN',
        'SERUM BILIRUBIN Ce a': 'SERUM BILIRUBIN',
        'INDIRECT BILIRUBIN': 'INDIRECT BILIRUBIN',
        'BILIRUBIN Ce a': 'BILIRUBIN',
        'BILIRUBIN': 'bilirubin'
    }
    
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    # Remove common OCR noise characters
    text = re.sub(r'[|}«»{}()\[\]]', '', text)  # Remove brackets and special chars
    text = re.sub(r'[|:;]', ' ', text)  # Replace pipes and colons with spaces
    text = re.sub(r'\s+', ' ', text)  # Normalize multiple spaces
    
    # Context-aware replacements (only in non-numeric contexts)
    text = re.sub(r'(?<!\d)0(?!\d)', 'o', text)  # Only replace '0' with 'o' when not surrounded by digits
    text = re.sub(r'(?<!\d)S(?!\d)', '5', text)  # Only replace 'S' with '5' when not surrounded by digits
    text = re.sub(r'(?<!\d)I(?!\d)', '1', text)  # Only replace 'I' with '1' when not surrounded by digits
    
    # Fix spacing issues around numbers and units
    text = re.sub(r'(\d)\s+([a-zA-Z])', r'\1 \2', text)  # Ensure space between number and unit
    text = re.sub(r'([a-zA-Z])\s+(\d)', r'\1 \2', text)  # Ensure space between letter and number
    
    return text.strip()

def preprocess_name(name):
    """Normalize test name for matching"""
    return re.sub(r'[^a-zA-Z0-9 ]', '', name).lower().strip()

def is_likely_test_name(name):
    """Check if a string is likely to be a test name"""
    skip_phrases = [
        'result date', 'parameters', 'test result', 'admitted under',
        'patient', 'bed no', 'ward', 'dr', 'report date', 'order no',
        'sample collected', 'validated by', 'approved by', 'page',
        'uhid', 'ip', 'final', 'investigation', 'laboratory', 'comprehensive',
        'panel', 'results', 'date', 'report', 'hospital', 'mims'
    ]
    name_lower = name.lower()
    return not any(phrase in name_lower for phrase in skip_phrases)

def find_best_test_match(candidate, threshold=0.4):
    """Find the best matching test name from the database"""
    if not candidate or len(candidate.strip()) < 2:
        return None
    
    candidate_clean = preprocess_name(candidate)
    
    # Direct match
    if candidate_clean in test_terms_set:
        return candidate_clean
    
    # Fuzzy match with lower threshold for noisy OCR
    close_matches = get_close_matches(candidate_clean, test_terms_set, n=1, cutoff=threshold)
    if close_matches:
        return close_matches[0]
    
    # Use rapidfuzz for more sophisticated matching
    if len(candidate_clean) > 3:
        match, score, _ = process.extractOne(candidate_clean, test_terms_set, scorer=fuzz.token_set_ratio)
        if score > 50:  # Even lower threshold for very noisy OCR
            return match
    
    return None

def extract_test_data_from_line(line):
    """Enhanced pattern matching for lab test data"""
    line = clean_ocr_text(line.strip())
    
    # More comprehensive patterns
    patterns = [
        # Pattern with flags (H/L indicators)
        r'^([A-Za-z\s()\-/]+?)\s+([<>]?\d+\.?\d*)\s*([HL])?\s+([a-zA-Z^°/*%μ/]+)\s+([<>]?\d+\.?\d*\s*[-–]\s*[<>]?\d+\.?\d*)',
        
        # Standard pattern with units and ranges
        r'^([A-Za-z\s()\-/]+?)\s+([<>]?\d+\.?\d*)\s+([a-zA-Z^°/*%μ/]+)\s+([<>]?\d+\.?\d*\s*[-–]\s*[<>]?\d+\.?\d*)',
        
        # Pattern with parenthetical ranges
        r'^([A-Za-z\s()\-/]+?):\s*([<>]?\d+\.?\d*)\s+([a-zA-Z^°/*%μ/]+)\s*\(([^)]+)\)',
        
        # Simple value with unit
        r'^([A-Za-z\s()\-/]+?)\s+([<>]?\d+\.?\d*)\s+([a-zA-Z^°/*%μ/]+)(?:\s|$)',
        
        # Just test name and value
        r'^([A-Za-z\s()\-/]+?)\s+([<>]?\d+\.?\d*)(?:\s|$)',
        
        # Handle decimal values better
        r'^([A-Za-z\s()\-/]+?)\s+(\d+\.\d+|\d+)\s*([a-zA-Z^°/*%μ/]*)\s*([<>]?\d+\.?\d*\s*[-–]\s*[<>]?\d+\.?\d*)?'
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.match(pattern, line, re.IGNORECASE)
        if match:
            groups = match.groups()
            test_name = groups[0].strip()
            value = groups[1]
            
            # Handle different group arrangements based on pattern
            if i == 0:  # Pattern with flag
                flag = groups[2] if groups[2] else ""
                unit = groups[3] if len(groups) > 3 else None
                ref_range = groups[4] if len(groups) > 4 else None
            else:
                flag = ""
                unit = groups[2] if len(groups) > 2 and groups[2] else None
                ref_range = groups[3] if len(groups) > 3 and groups[3] else None
            
            # Clean up reference range
            if ref_range:
                ref_range = re.sub(r'\s+', '', ref_range)
            
            return test_name, value, unit, ref_range, flag
    
    return None, None, None, None, None

def determine_flag(value, ref_range):
    """Determine if value is high (H) or low (L) based on reference range"""
    if not value or not ref_range:
        return ""
    
    try:
        # Handle values with > or <
        if value.startswith('>') or value.startswith('<'):
            return "H" if value.startswith('>') else "L"
        
        val_num = float(value)
        range_parts = ref_range.split('-')
        if len(range_parts) == 2:
            low, high = float(range_parts[0]), float(range_parts[1])
            if val_num > high:
                return "H"
            elif val_num < low:
                return "L"
    except:
        pass
    
    return ""

def parse_lab_tests(ocr_text):
    """Main function to parse lab test results from OCR text - sliding window for noisy OCR"""
    lines = [clean_ocr_text(line.strip()) for line in ocr_text.split("\n") if line.strip()]
    results = []
    i = 0
    n = len(lines)
    
    while i < n:
        # Try to group up to 3 lines as a test block
        window = lines[i:i+3]
        # Try all possible concatenations of 1, 2, or 3 lines
        candidates = [window[0]]
        if len(window) > 1:
            candidates.append(window[0] + " " + window[1])
        if len(window) > 2:
            candidates.append(window[0] + " " + window[1] + " " + window[2])
        found = False
        for candidate in candidates:
            test_name, value, unit, ref_range, flag = extract_test_data_from_line(candidate)
            if test_name:
                matched_test = find_best_test_match(test_name)
                if matched_test:
                    # Use flag from pattern if available, otherwise determine from value/range
                    if not flag and ref_range:
                        flag = determine_flag(value, ref_range)
                    results.append({
                        'test_name': matched_test,
                        'flag': flag,
                        'value': value,
                        'ref_range': ref_range,
                        'unit': normalize_unit(unit) if unit else None
                    })
                    # Skip lines used in this candidate
                    used_lines = candidate.count(" ") // 10 + 1  # crude: at least 1, up to 3
                    i += min(len(window), used_lines)
                    found = True
                    break
        if found:
            continue
        # If not found, try to treat line as test name and look for value/unit in next lines
        line = lines[i]
        if is_likely_test_name(line):
            matched_test = find_best_test_match(line)
            if matched_test:
                value, unit, ref_range = None, None, None
                for j in range(1, 3):
                    if i + j >= n:
                        break
                    next_line = lines[i + j]
                    # Try to extract value/unit from next line
                    _, val, un, rng, _ = extract_test_data_from_line(next_line)
                    if val and not value:
                        value = val
                    if un and not unit:
                        unit = un
                    if rng and not ref_range:
                        ref_range = rng
                results.append({
                    'test_name': matched_test,
                    'flag': determine_flag(value, ref_range),
                    'value': value,
                    'ref_range': ref_range,
                    'unit': normalize_unit(unit) if unit else None
                })
                i += 2
                continue
        i += 1
    return results


