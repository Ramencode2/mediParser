import logging
from .ocr_utils import extract_text_with_easyocr, clean_ocr_text

logger = logging.getLogger(__name__)

def format_result(res):
    """Format a test result with improved out-of-range detection."""
    # Get the raw value and any flag
    test_value = res.get("value", "")
    flag = res.get("flag", "")
    
    # Handle the case where the value might include a flag
    if isinstance(test_value, str):
        test_value = test_value.replace('*', '').strip()
    
    return {
        "test_name": res.get("test_name"),
        "test_value": test_value,
        "bio_reference_range": res.get("ref_range"),
        "test_unit": res.get("unit"),
        "lab_test_out_of_range": is_test_out_of_range(
            test_value,
            res.get("ref_range"),
            flag
        )
    }

def is_test_out_of_range(value, ref_range, flag=''):
    """
    Determine if a test value is out of range based on the reference range and flags.
    
    Args:
        value (str): The test value
        ref_range (str): The reference range
        flag (str): Any flag associated with the value ('H', 'L', '*', etc.)
    
    Returns:
        bool: True if the value is out of range, False otherwise
    """
    # If any input is None or empty, we can't determine if it's out of range
    if not value or not ref_range:
        return False

    # First check if there's an explicit flag indicating out of range
    if flag and any(f in flag.upper() for f in ['H', 'L', '*', '↑', '↓']):
        return True
        
    # Check if the value has an asterisk or flag embedded
    if isinstance(value, str) and any(char in value for char in ['*', 'H', 'L', '↑', '↓']):
        return True
    
    try:
        # Clean the value and convert to float
        cleaned_value = str(value).replace('*', '').strip()
        
        # Handle special cases like "<0.01" in the value
        if any(char in cleaned_value for char in ['<', '>']):
            # For now, treat these as in range as they're usually within acceptable limits
            return False
            
        val = float(cleaned_value)
        
        # If we have a reference range, parse it
        if ref_range:
            # Standardize the reference range format
            ref_range = ref_range.strip().replace('–', '-')  # Handle en-dash
            ref_range = ref_range.replace('−', '-')  # Handle minus sign
            
            # Try different range formats
            if '-' in ref_range:
                # Handle hyphen format (e.g., "0.0-7.0")
                parts = ref_range.split('-')
                if len(parts) == 2:
                    try:
                        low, high = map(float, parts)
                        return val < low or val > high
                    except ValueError:
                        # If conversion fails, might be a complex range
                        pass
                        
            elif ' ' in ref_range and len(ref_range.split()) == 2:
                # Handle space-separated format (e.g., "0.0 7.0")
                try:
                    low, high = map(float, ref_range.split())
                    return val < low or val > high
                except ValueError:
                    pass
                    
            elif 'to' in ref_range.lower():
                # Handle 'to' format (e.g., "0.0 to 7.0")
                parts = ref_range.lower().split('to')
                try:
                    low = float(parts[0].strip())
                    high = float(parts[1].strip())
                    return val < low or val > high
                except ValueError:
                    pass
                    
            # Check for comparison format
            elif '<' in ref_range or '≤' in ref_range:
                try:
                    limit = float(ref_range.replace('<', '').replace('≤', '').strip())
                    return val > limit  # If reference is "<10", then 11 is out of range
                except ValueError:
                    pass
                    
            elif '>' in ref_range or '≥' in ref_range:
                try:
                    limit = float(ref_range.replace('>', '').replace('≥', '').strip())
                    return val < limit  # If reference is ">20", then 19 is out of range
                except ValueError:
                    pass
                    
            # Handle ranges with text (e.g., "Negative" or "Non-reactive")
            elif any(word in ref_range.lower() for word in ['negative', 'non-reactive', 'normal']):
                # These are typically qualitative tests
                # Consider them out of range if they don't match exactly
                return str(value).lower() not in ref_range.lower()
                
    except (ValueError, TypeError):
        # If we can't parse the numbers, fall back to string comparison
        if ref_range and str(value).strip().lower() != ref_range.strip().lower():
            return True
        
    return False
