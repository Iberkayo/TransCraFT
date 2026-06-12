import re
from collections import Counter

def normalize_term(term: str) -> str:
    """Normalize a terminology string by removing articles and punctuation."""
    # Strip punctuation
    term = re.sub(r'[^\w\s-]', '', term)
    
    # Remove leading articles case-insensitively
    term = re.sub(r'^(the|a|an)\s+', '', term, flags=re.IGNORECASE)
    
    return term.strip()

def extract_fallback_terms(text: str) -> list[str]:
    """Extract repeated capitalized multi-word terms, acronyms, and hyphenated terms."""
    cap_multi = re.findall(r'\b(?:[A-Z][a-z]+ ){1,3}[A-Z][a-z]+\b', text)
    acronyms = re.findall(r'\b[A-Z]{2,5}\b', text)
    hyphenated = re.findall(r'\b[A-Z]?[a-z]+-[a-zA-Z]+\b', text)
    
    all_raw_candidates = cap_multi + acronyms + hyphenated
    
    # Normalize and merge variants
    normalized_counts = Counter()
    canonical_map = {} # Maps lowercase to the most preferred clean form
    
    for raw in all_raw_candidates:
        norm = normalize_term(raw)
        if not norm:
            continue
            
        lower_norm = norm.lower()
        normalized_counts[lower_norm] += 1
        
        # Prefer the version with proper capitalization if not set, or keep existing if it's already Title Case
        if lower_norm not in canonical_map:
            canonical_map[lower_norm] = norm
        else:
            # If current canonical is all lowercase but new norm has caps, prefer the caps
            if canonical_map[lower_norm].islower() and not norm.islower():
                canonical_map[lower_norm] = norm
                
    # Filter terms that appear more than once
    final_candidates = []
    for lower_norm, count in normalized_counts.items():
        if count > 1:
            # Avoid overly generic 1-word non-acronym terms if they crept in
            canonical = canonical_map[lower_norm]
            if len(canonical) > 2:
                final_candidates.append(canonical)
                
    return final_candidates
