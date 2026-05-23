#!/usr/bin/env python3
"""
Validation script to ensure data loads correctly and all expected columns are present.
"""
import os
import sys
from pathlib import Path

# Set the correct DATA_DIR
os.environ['DATA_DIR'] = str(Path(__file__).parent.parent / 'data' / 'raw' / 'data')

from app.data.store import DataStore
from app.services.conversion_engine import ConversionEngine
from app.services.opportunity_engine import OpportunityEngine
from app.services.kol_engine import KOLEngine

def validate_data_loading():
    """Validate that all data is loaded correctly."""
    print("=" * 80)
    print("VALIDATING DATA LOADING")
    print("=" * 80)
    
    store = DataStore.instance()
    store.load_all()
    
    counts = store.counts()
    print(f"\nData Rows Loaded:")
    for table, count in counts.items():
        status = "✓" if count > 0 else "✗"
        print(f"  {status} {table}: {count} rows")
    
    # Check key tables are not empty
    errors = []
    for table in ['hcp_master', 'field_interactions_source', 'prescription_claims_source']:
        if counts.get(table, 0) == 0:
            errors.append(f"Missing data in {table}")
    
    return errors

def validate_column_availability():
    """Validate that all expected columns exist."""
    print("\n" + "=" * 80)
    print("VALIDATING COLUMN AVAILABILITY")
    print("=" * 80)
    
    store = DataStore.instance()
    conv_eng = ConversionEngine()
    opp_eng = OpportunityEngine()
    kol_eng = KOLEngine()
    
    errors = []
    
    # Check hcp_master columns
    print("\nhcp_master columns:")
    hcp_df = store.df("hcp_master")
    expected_hcp_cols = ['hcp_id', 'hcp_name', 'specialty_group', 'territory', 'region', 'consent_status']
    for col in expected_hcp_cols:
        if col in hcp_df.columns:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ {col} (MISSING)")
            errors.append(f"hcp_master missing column: {col}")
    
    # Check conversion calls
    print("\nConversionEngine.calls() columns:")
    calls = conv_eng.calls()
    if not calls.empty:
        expected_call_cols = ['interaction_id', 'hcp_id', 'rep_id', 'interaction_datetime', 'converted']
        for col in expected_call_cols:
            if col in calls.columns:
                print(f"  ✓ {col}")
            else:
                print(f"  ✗ {col} (MISSING)")
                errors.append(f"ConversionEngine.calls() missing column: {col}")
    else:
        print("  ✗ No data loaded")
        errors.append("ConversionEngine.calls() returned empty dataframe")
    
    # Check opportunity scores
    print("\nOpportunityEngine.score_all() columns:")
    opps = opp_eng.score_all()
    if not opps.empty:
        expected_opp_cols = ['hcp_id', 'hcp_name', 'specialty_group', 'opportunity_score']
        for col in expected_opp_cols:
            if col in opps.columns:
                print(f"  ✓ {col}")
            else:
                print(f"  ✗ {col} (MISSING)")
                errors.append(f"OpportunityEngine.score_all() missing column: {col}")
    else:
        print("  ✗ No data loaded")
        errors.append("OpportunityEngine.score_all() returned empty dataframe")
    
    # Check KOL data
    print("\nKOLEngine.profile() availability:")
    kols = store.df("kol_master")
    if not kols.empty:
        print(f"  ✓ kol_master loaded ({len(kols)} rows)")
    else:
        print("  ✗ kol_master empty")
        errors.append("kol_master is empty")
    
    return errors

def main():
    """Run all validations."""
    all_errors = []
    
    # Validate data loading
    loading_errors = validate_data_loading()
    all_errors.extend(loading_errors)
    
    # Validate columns
    column_errors = validate_column_availability()
    all_errors.extend(column_errors)
    
    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    if all_errors:
        print(f"\n✗ Found {len(all_errors)} errors:\n")
        for error in all_errors:
            print(f"  - {error}")
        return 1
    else:
        print("\n✓ All validations passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
