import re
from rapidfuzz import fuzz
import logging
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class TestResult:
    """Structured representation of a lab test result."""
    test_name: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = None
    confidence: float = 0.0
    raw_text: str = ""

class MedicalDocumentParser:
    """Enhanced parser for various types of medical documents."""
    
    def __init__(self):
        self.common_units = {
            'mg/dl', 'g/dl', 'mmol/l', 'iu/ml', 'ng/ml', 'pg/ml', 'mcg/ml',
            'fl', 'pg', 'fmol/l', 'pmol/l', 'cells/ul', 'cells/mm3',
            'thousand/ul', 'million/ul', '%', 'ratio', 'index', 'score',
            'bpm', 'mmhg', 'cm', 'kg', 'lbs', 'celsius', 'fahrenheit',
            'copies/ml', 'log copies/ml', 'mu/ml', 'u/ml', 'ku/l', 'u/l',
            'mill/cmm', 'mill/cu.mm', '/ul', 'g/dl', 'mg/l', 'gm/dl',
            'iul', 'lu1', 'lul', '/l', 'mil/cumm', 'mill/cumm',
            'gldl', 'g/l', 'mg/dl', 'ng/dl', 'pg/dl',
            'fl', 'pg', 'g/dl', '/ul', '/mm3', '/cumm'
        }
        
        # Unit standardization map
        self.unit_standardization = {
            'gm/dl': 'g/dl',
            'gldl': 'g/dl',
            'g/l': 'g/dl',
            'mill/cmm': 'million/cmm',
            'mill/cu.mm': 'million/cmm',
            'mil/cumm': 'million/cumm',
            'mill/cumm': 'million/cumm',
            'iul': '/ul',
            'lu1': '/ul',
            'lul': '/ul',
            'ul': '/ul',
            '/cumm': '/mm3'
        }
        
        self.test_categories = {
            'hematology': [
                'hemoglobin', 'hb', 'hematocrit', 'hct', 'rbc', 'wbc', 
                'platelet', 'plt', 'mcv', 'mch', 'mchc', 'rdw', 
                'neutrophil', 'lymphocyte', 'monocyte', 'eosinophil', 
                'basophil', 'mpv', 'complete blood count', 'cbc'
            ],
            'chemistry': [
                'glucose', 'creatinine', 'urea', 'bun', 'sodium', 'na', 
                'potassium', 'k', 'chloride', 'cl', 'calcium', 'ca',
                'phosphorus', 'magnesium', 'albumin', 'total protein',
                'globulin', 'a/g ratio'
            ],
            'lipid': [
                'cholesterol', 'triglycerides', 'hdl', 'ldl', 'vldl',
                'total lipids', 'lipid profile'
            ],
            'liver': [
                'alt', 'ast', 'alp', 'ggt', 'bilirubin', 'total bilirubin',
                'direct bilirubin', 'indirect bilirubin', 'sgpt', 'sgot'
            ],
            'thyroid': [
                'tsh', 't3', 't4', 'ft3', 'ft4', 'thyroid', 
                'thyroid stimulating hormone'
            ],
            'cardiac': [
                'troponin', 'ck-mb', 'ck', 'cpk', 'ldh', 'bnp', 
                'nt-probnp', 'cardiac'
            ],
            'diabetes': [
                'hba1c', 'glucose', 'blood sugar', 'fbs', 'ppbs', 
                'random blood sugar', 'insulin'
            ],
            'inflammatory': [
                'esr', 'crp', 'procalcitonin', 'sed rate', 
                'erythrocyte sedimentation rate'
            ],
            'coagulation': [
                'pt', 'ptt', 'inr', 'fibrinogen', 'd-dimer', 'bleeding time',
                'clotting time', 'aptt'
            ]
        }

        # Add more test patterns
        self.test_patterns = [
            'COMPLETE BLOOD COUNT', 'CBC',
            'HEMOGLOBIN', 'HB',
            'RBC COUNT', 'RED BLOOD CELL',
            'HEMATOCRIT', 'HCT', 'PCV',
            'MCV', 'MEAN CORPUSCULAR VOLUME',
            'MCH', 'MEAN CORPUSCULAR HEMOGLOBIN',
            'MCHC', 'MEAN CORPUSCULAR HEMOGLOBIN CONCENTRATION',
            'RDW', 'RED CELL DISTRIBUTION WIDTH',
            'WBC COUNT', 'WHITE BLOOD CELL',
            'DIFFERENTIAL COUNT', 'DIFF COUNT',
            'NEUTROPHILS', 'NEUT',
            'LYMPHOCYTES', 'LYMP',
            'EOSINOPHILS', 'EOS',
            'MONOCYTES', 'MONO',
            'BASOPHILS', 'BASO',
            'PLATELETS', 'PLT',
            'MPV', 'MEAN PLATELET VOLUME',
            'SERUM', 'BLOOD',
            'BLOOD UREA', 'UREA',
            'CREATININE', 'CREA',
            'URIC ACID',
            'SODIUM', 'NA',
            'POTASSIUM', 'K',
            'CALCIUM', 'CA',
            'PHOSPHORUS', 'PHOS',
            'PROTEIN', 'TOTAL PROTEIN',
            'ALBUMIN', 'ALB',
            'GLOBULIN', 'GLOB'
        ]
        
    def clean_ocr_text(self, text: str) -> str:
        """Enhanced OCR error correction with medical-specific rules."""
        logging.info(f"[RAW OCR] {text}")
        if not text:
            return ""
        
        # Remove common OCR noise
        text = re.sub(r'[|}«»{}()\[\]]+', '', text)
        text = re.sub(r'[|:;]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Medical-specific OCR corrections
        ocr_corrections = {
            # Common character misreads
            r'(?<!\d)0(?=\s|$)': 'O',  # 0 to O at word boundaries
            r'(?<!\d)S(?=\s|\d)': '5',  # S to 5 before digits
            r'(?<!\d)I(?=\s|\d)': '1',  # I to 1 before digits
            r'(?<!\d)l(?=\s|\d)': '1',  # l to 1 before digits
            r'(?<=\d)O(?=\s|$)': '0',   # O to 0 after digits
            r'(?<=\d)o(?=\s|$)': '0',   # o to 0 after digits
            
            # Medical term corrections
            r'\bHaemoglobin\b': 'Hemoglobin',
            r'\bHaematocrit\b': 'Hematocrit',
            r'\bR\.B\.C\b': 'RBC',
            r'\bW\.B\.C\b': 'WBC',
            r'\bmillcmm\b': 'mill/cmm',
            r'\bmicro\s*gram\b': 'mcg',
            r'\bmicro\s*liter\b': 'mcl',
            
            # Unit corrections
            r'\bmg\s*%\s*dl\b': 'mg/dl',
            r'\bg\s*%\s*dl\b': 'g/dl',
            r'\bmmol\s*l\b': 'mmol/l',
            r'\biu\s*ml\b': 'iu/ml',
            r'\bng\s*ml\b': 'ng/ml',
            r'\bpg\s*ml\b': 'pg/ml',
            r'\bmcg\s*ml\b': 'mcg/ml',
            r'\bcells\s*ul\b': 'cells/ul',
            r'\bthousand\s*ul\b': 'thousand/ul',
            r'\bmillion\s*ul\b': 'million/ul',
            
            # Range separators
            r'\s*-\s*': '-',
            r'\s*–\s*': '-',
            r'\s*—\s*': '-',
            r'\s*to\s*': '-',
        }
        
        for pattern, replacement in ocr_corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Fix spacing around numbers and units
        text = re.sub(r'(\d)\s+([a-zA-Z/%])', r'\1 \2', text)
        text = re.sub(r'([a-zA-Z])\s+(\d)', r'\1 \2', text)
        
        return text.strip()

    def extract_test_data_from_line(self, line: str) -> Optional[TestResult]:
        """Enhanced pattern matching for various medical test formats."""
        line = self.clean_ocr_text(line.strip())

        if not line or len(line) < 5:
            return None

        # Common test result patterns in lab reports
        patterns = [
            # Standard format: Test Name | Value [Flag] Unit | Range
            r'([A-Za-z][\w\s\-\(\)\/,.]+?)\s+([\d\.]+)\s*\[?([HLhl\*]?)\]?\s*([\w/%\.]+)?\s*([\d\.-]+\s*-\s*[\d\.]+)?',
            
            # Format with range at end: Test Name | Value Unit | Range
            r'([A-Za-z][\w\s\-\(\)\/,.]+?)\s+([\d\.]+)\s*([\w/%\.]+)?\s+([\d\.-]+\s*-\s*[\d\.]+)',
            
            # Format with flag after value: Test Name | Value Flag Unit
            r'([A-Za-z][\w\s\-\(\)\/,.]+?)\s+([\d\.]+)\s*([HLhl\*])\s*([\w/%\.]+)',
            
            # Simple format: Test Name | Value Unit
            r'([A-Za-z][\w\s\-\(\)\/,.]+?)\s+([\d\.]+)\s*([\w/%\.]+)',
        ]

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                test_name = self.clean_test_name(groups[0])
                
                # Extract core components
                value = groups[1]
                
                # Handle different pattern formats
                if len(groups) >= 4:
                    flag = groups[2] if groups[2] in 'HLhl*' else ''
                    unit = groups[2] if not flag else groups[3]
                    ref_range = groups[4] if len(groups) > 4 else None
                else:
                    flag = ''
                    unit = groups[2] if len(groups) > 2 else None
                    ref_range = None
                
                # Clean up unit
                if unit:
                    unit = unit.strip().lower()
                    # Standardize common unit variations
                    unit_replacements = {
                        'gm/dl': 'g/dl',
                        'gm/dl': 'g/dl',
                        'mill/cmm': 'million/cmm',
                        'mill/cu.mm': 'million/cmm',
                        'iul': '/ul',
                        'lu1': '/ul',
                        'ul': '/ul',
                    }
                    unit = unit_replacements.get(unit, unit)
                
                # Calculate confidence
                confidence = self.calculate_confidence(test_name, value, unit, ref_range, flag)
                
                if self.is_valid_test_name(test_name):
                    return TestResult(
                        test_name=test_name,
                        value=value,
                        unit=unit,
                        reference_range=ref_range,
                        flag=flag,
                        confidence=confidence,
                        raw_text=line
                    )
        return None

    def clean_test_name(self, name: str) -> str:
        """Clean and normalize test names."""
        if not name:
            return name
            
        name = name.strip()
        
        # Remove common prefixes/suffixes
        name = re.sub(r'^(test|result|level)[\s:]+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'[\s:]+$', '', name)
        
        # Clean up common OCR errors
        name = name.replace('1', 'l')  # Replace mistaken 1's with l's
        name = re.sub(r'[-\s]+ta[l1]$', '', name)  # Remove -tal suffix from OCR errors
        
        # Remove artifacts
        name = re.sub(r'\{#\}', '', name)  # Remove {#}
        name = re.sub(r'\([^)]*\)$', '', name)  # Remove trailing parentheses
        name = re.sub(r'[\s:]+$', '', name)  # Remove trailing colons and spaces
        
        # Handle common variations and abbreviations
        replacements = {
            'hb': 'Hemoglobin',
            'haemoglobin': 'Hemoglobin',
            'wbc': 'White Blood Cell',
            'rbc': 'Red Blood Cell',
            'r.b.c.': 'Red Blood Cell',
            'w.b.c.': 'White Blood Cell',
            'plt': 'Platelet',
            'mcv': 'Mean Corpuscular Volume',
            'mc.v': 'Mean Corpuscular Volume',
            'mch': 'Mean Corpuscular Hemoglobin',
            'mc.h': 'Mean Corpuscular Hemoglobin',
            'mchc': 'Mean Corpuscular Hemoglobin Concentration',
            'mc.h.c': 'Mean Corpuscular Hemoglobin Concentration',
            'rdw': 'Red Cell Distribution Width',
            'r.d.w': 'Red Cell Distribution Width',
            'mpv': 'Mean Platelet Volume',
            'hct': 'Hematocrit',
            'haematocrit': 'Hematocrit',
            'pcv': 'Hematocrit',
            'neut': 'Neutrophils',
            'lymph': 'Lymphocytes',
            'mono': 'Monocytes',
            'eos': 'Eosinophils',
            'baso': 'Basophils',
            'differential count': 'Differential Count',
            'absolute count': 'Absolute Count'
        }
        
        # Try exact match first
        name_lower = name.lower()
        if name_lower in replacements:
            return replacements[name_lower]
            
        # Try partial matches
        for abbr, full in replacements.items():
            if re.search(rf'\b{re.escape(abbr)}\b', name_lower):
                return full
        
        # Clean up the name
        name = re.sub(r'\s*\([^)]*\)\s*$', '', name)  # Remove parenthetical at end
        name = re.sub(r'\s*#\s*$', '', name)  # Remove trailing #
        name = re.sub(r'\s+', ' ', name)  # Normalize spaces
        name = name.strip()
        
        # Special case for "Total X Count"
        if re.match(r'^total\s+.*\s+count$', name_lower):
            return name.title()
        
        return name

    def determine_flag(self, value: str, ref_range: str) -> str:
        """Enhanced flag determination with better error handling."""
        if not value or not ref_range:
            return ""
        try:
            # Handle comparison operators in value
            if value.startswith('>') or value.startswith('≥'):
                return "H"
            elif value.startswith('<') or value.startswith('≤'):
                return "L"

            # Parse numeric value
            val_num = float(re.sub(r'[^\d.]', '', value))

            # Parse reference range
            range_match = re.match(r'([<>≤≥]?\d+\.?\d*)\s*[-–]\s*([<>≤≥]?\d+\.?\d*)', ref_range)
            if range_match:
                low_str, high_str = range_match.groups()
                low = float(re.sub(r'[^\d.]', '', low_str))
                high = float(re.sub(r'[^\d.]', '', high_str))

                if val_num > high:
                    return "H"
                elif val_num < low:
                    return "L"
                else:
                    return "N"  # Normal
        except (ValueError, AttributeError):
            pass
        return ""

    def calculate_confidence(self, test_name: str, value: str, unit: str, ref_range: str, flag: str) -> float:
        """Calculate confidence score for extracted test result."""
        confidence = 0.0
        
        # Base confidence for having test name and value
        if test_name and value:
            confidence += 0.4
        
        # Additional confidence for complete data
        if unit:
            confidence += 0.2
        if ref_range:
            confidence += 0.2
        if flag:
            confidence += 0.1
        
        # Bonus for recognized test names
        test_name_lower = test_name.lower()
        for category, tests in self.test_categories.items():
            if any(test in test_name_lower for test in tests):
                confidence += 0.1
                break
        
        return min(confidence, 1.0)

    def is_valid_test_name(self, name: str) -> bool:
        """Enhanced validation for test names."""
        name = name.strip()
        
        # Basic validation
        if not name or len(name) < 2:
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', name):
            return False
        
        # Reject if all numbers/symbols
        if all(char in '0123456789.- /' for char in name):
            return False
        
        # Reject common false positives
        invalid_patterns = [
            r'^\d+$',  # Only numbers
            r'^[.\-\s]+$',  # Only punctuation
            r'^(ul|ml|dl|l|mg|g|ng|pg|mcg|kg|lbs)$',  # Only units
            r'^(a|an|the|and|or|of|in|on|at|to|for|with|by)$',  # Articles/prepositions
            r'^(normal|abnormal|high|low|positive|negative)$',  # Result descriptors
            r'^(page|report|lab|test|result|value|range|reference)$',  # Document terms
            r'^(date|time|patient|doctor|physician|hospital|clinic)$',  # Header terms
        ]
        
        name_lower = name.lower()
        for pattern in invalid_patterns:
            if re.match(pattern, name_lower):
                return False
        
        # Reject very short common words
        if len(name) <= 3 and name_lower in {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}:
            return False
        
        return True

    def parse_document(self, text: str) -> List[TestResult]:
        """Enhanced document parsing with better handling of tabular formats."""
        if not text:
            return []
            
        # Clean the text first
        text = self.clean_ocr_text(text)
        
        # Split into lines
        lines = text.split('\n')
        results = []
        
        # Variables to track test information
        test_names = []
        test_values = []
        test_units = []
        test_flags = []
        test_ranges = []
        in_test_section = False
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if 'COMPLETE BLOOD COUNT' in line.upper():
                in_test_section = True
                current_section = 'COMPLETE BLOOD COUNT'
                continue
            elif 'DIFFERENTIAL' in line.upper() and 'COUNT' in line.upper():
                current_section = 'DIFFERENTIAL COUNT'
                continue
            elif 'ABSOLUTE' in line.upper() and 'COUNT' in line.upper():
                current_section = 'ABSOLUTE COUNT'
                continue
            
            if not in_test_section:
                continue
            
            # Check if line contains a test name
            test_name_match = re.match(r'^(.*?(?:Count|Volume|Width|Hb|Distribution|Haemoglobin|Haematocrit|Neutrophils|Lymphocytes|Eosinophils|Monocytes|Basophils|Platelets|MPV|FRACTION).*?)(?:\s+(\d+\.?\d*)(?:\s*\[([HLhl\*])\])?\s*([\w/%\.]+))?$', line)
            if test_name_match:
                name = test_name_match.group(1).strip()
                value = test_name_match.group(2)
                flag = test_name_match.group(3)
                unit = test_name_match.group(4)
                
                if value:  # If we have a value on the same line
                    results.append(TestResult(
                        test_name=self.clean_test_name(name),
                        value=value,
                        unit=unit,
                        flag=flag if flag else "",
                        confidence=0.8,  # High confidence for direct matches
                        raw_text=line
                    ))
                else:  # Store the test name for later matching
                    test_names.append(name)
            
            # Check if line contains a value and reference range
            elif test_names and re.match(r'^\s*[\d\.]+\s*\[?[HLhl\*]?\]?\s*[\w/%\.]+\s*(?:[\d\.-]+\s*-\s*[\d\.]+)?', line):
                parts = line.split()
                value = parts[0]
                flag = ""
                unit = None
                ref_range = None
                
                # Extract flag if present
                if len(parts) > 1 and re.match(r'\[[HLhl\*]\]', parts[1]):
                    flag = parts[1].strip('[]')
                    parts = parts[0:1] + parts[2:]
                
                # Extract unit and reference range
                if len(parts) > 1:
                    unit = parts[1]
                if len(parts) > 2:
                    ref_range = ' '.join(parts[2:])
                
                # Match with the last unmatched test name
                test_name = test_names.pop(0)
                results.append(TestResult(
                    test_name=self.clean_test_name(test_name),
                    value=value,
                    unit=unit,
                    reference_range=ref_range,
                    flag=flag,
                    confidence=0.8,  # High confidence for matched pairs
                    raw_text=line
                ))
            
            # Handle reference ranges on separate lines
            elif results and re.match(r'^\s*[\d\.-]+\s*-\s*[\d\.]+\s*[\w/%\.]+', line):
                parts = line.split()
                if len(parts) >= 2:
                    range_str = ' '.join(parts[:-1])
                    unit = parts[-1]
                    results[-1].reference_range = range_str
                    if not results[-1].unit:
                        results[-1].unit = unit
        
        return results
    
    def process_section(self, section_name: str, lines: List[str]) -> List[TestResult]:
        """Process a section of related test results."""
        results = []
        
        # Join lines that might be split incorrectly
        processed_lines = []
        current_line = ''
        
        for line in lines:
            # If line contains a number and unit, it's likely a complete test result
            if re.search(r'\d+\.?\d*\s*[a-zA-Z/%]+', line):
                if current_line:
                    processed_lines.append(current_line)
                current_line = line
            else:
                current_line = (current_line + ' ' + line).strip()
        
        if current_line:
            processed_lines.append(current_line)
        
        # Process each line
        for line in processed_lines:
            result = self.extract_test_data_from_line(line)
            if result:
                # Add section context if missing
                if section_name and not any(p.lower() in result.test_name.lower() for p in self.test_patterns):
                    result.test_name = f"{section_name} {result.test_name}"
                results.append(result)
        
        return results
    
    def group_by_category(self, results: List[TestResult]) -> Dict[str, List[TestResult]]:
        """Group test results by their categories."""
        categorized = {}
        
        for result in results:
            category = 'other'  # Default category
            test_name_lower = result.test_name.lower()
            
            # Check each category's tests
            for cat, tests in self.test_categories.items():
                if any(test.lower() in test_name_lower for test in tests):
                    category = cat
                    break
                    
            # Special case handling for common test names
            if any(term in test_name_lower for term in ['blood count', 'cbc', 'complete blood']):
                category = 'hematology'
            elif any(term in test_name_lower for term in ['kidney', 'renal', 'kft']):
                category = 'chemistry'
            elif any(term in test_name_lower for term in ['liver', 'hepatic', 'lft']):
                category = 'liver'
            elif any(term in test_name_lower for term in ['thyroid', 'tsh', 't3', 't4']):
                category = 'thyroid'
            elif any(term in test_name_lower for term in ['lipid', 'cholesterol', 'triglyceride']):
                category = 'lipid'
            elif any(term in test_name_lower for term in ['sugar', 'glucose', 'hba1c']):
                category = 'diabetes'
            
            # Initialize category if not exists
            if category not in categorized:
                categorized[category] = []
            
            categorized[category].append(result)
        
        return categorized