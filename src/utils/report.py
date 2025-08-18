import json
import datetime
import csv
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

def generate_translation_report(english_texts: List[str], japanese_texts: List[str], 
                              ignored_words: List[str], url: str) -> Dict[str, Any]:
    """Generate comprehensive translation report"""
    
    # Clean and filter texts
    english_clean = [text for text in english_texts if text and len(text.strip()) > 2]
    japanese_clean = [text for text in japanese_texts if text and len(text.strip()) > 2]
    
    # Analyze translations
    not_translated = []
    translated = []
    ignored = []
    
    # Create pairs for comparison (assuming same order)
    max_len = max(len(english_clean), len(japanese_clean))
    
    for i in range(max_len):
        en_text = english_clean[i] if i < len(english_clean) else ""
        jp_text = japanese_clean[i] if i < len(japanese_clean) else ""
        
        # Skip if text is in ignored words
        if any(ignored_word.lower() in en_text.lower() for ignored_word in ignored_words):
            ignored.append({"english": en_text, "japanese": jp_text})
            continue
        
        # Check if translated (contains Japanese characters)
        if jp_text and any(ord(char) > 127 for char in jp_text):
            translated.append({"english": en_text, "japanese": jp_text})
        else:
            not_translated.append({"english": en_text, "japanese": jp_text})
    
    # Calculate coverage
    total_analyzed = len(translated) + len(not_translated)
    coverage = (len(translated) / max(total_analyzed, 1)) * 100
    
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "url": url,
        "summary": {
            "total_texts": len(english_clean),
            "translated": len(translated),
            "not_translated": len(not_translated),
            "ignored": len(ignored),
            "coverage_percent": round(coverage, 2)
        },
        "details": {
            "translated": translated[:50],  # Limit to first 50
            "not_translated": not_translated[:50],  # Limit to first 50
            "ignored": ignored[:20]  # Limit to first 20
        }
    }
    
    return report

def save_json_report(report: Dict[str, Any], filename: str = "translation_report.json"):
    """Save report as JSON"""
    Path("reports").mkdir(exist_ok=True)
    filepath = Path("reports") / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 JSON report saved: {filepath}")
    return filepath

def save_excel_report(report: Dict[str, Any], filename: str = "translation_report.xlsx"):
    """Save report as Excel with multiple sheets"""
    Path("reports").mkdir(exist_ok=True)
    filepath = Path("reports") / filename
    
    # Create Excel writer
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        
        # Summary sheet
        summary_data = {
            "Metric": ["Total Texts", "Translated", "Not Translated", "Ignored", "Coverage %"],
            "Value": [
                report["summary"]["total_texts"],
                report["summary"]["translated"],
                report["summary"]["not_translated"],
                report["summary"]["ignored"],
                report["summary"]["coverage_percent"]
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        
        # Translated texts sheet
        if report["details"]["translated"]:
            translated_df = pd.DataFrame(report["details"]["translated"])
            translated_df.to_excel(writer, sheet_name="Translated", index=False)
        
        # Not translated texts sheet
        if report["details"]["not_translated"]:
            not_translated_df = pd.DataFrame(report["details"]["not_translated"])
            not_translated_df.to_excel(writer, sheet_name="Not_Translated", index=False)
        
        # Ignored texts sheet
        if report["details"]["ignored"]:
            ignored_df = pd.DataFrame(report["details"]["ignored"])
            ignored_df.to_excel(writer, sheet_name="Ignored", index=False)
    
    print(f"📊 Excel report saved: {filepath}")
    return filepath

def save_csv_report(report: Dict[str, Any], filename: str = "translation_report.csv"):
    """Save report as CSV"""
    Path("reports").mkdir(exist_ok=True)
    filepath = Path("reports") / filename
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(["Type", "English Text", "Japanese Text"])
        
        # Write translated texts
        for item in report["details"]["translated"]:
            writer.writerow(["Translated", item["english"], item["japanese"]])
        
        # Write not translated texts
        for item in report["details"]["not_translated"]:
            writer.writerow(["Not Translated", item["english"], item["japanese"]])
        
        # Write ignored texts
        for item in report["details"]["ignored"]:
            writer.writerow(["Ignored", item["english"], item["japanese"]])
    
    print(f"📋 CSV report saved: {filepath}")
    return filepath

def generate_comprehensive_report(english_texts: List[str], japanese_texts: List[str], 
                                ignored_words: List[str], url: str):
    """Generate and save all report formats"""
    
    # Generate report
    report = generate_translation_report(english_texts, japanese_texts, ignored_words, url)
    
    # Save in multiple formats
    json_file = save_json_report(report)
    excel_file = save_excel_report(report)
    csv_file = save_csv_report(report)
    
    # Print summary
    print(f"\n🎯 Translation Report Summary:")
    print(f"   URL: {url}")
    print(f"   Total Texts: {report['summary']['total_texts']}")
    print(f"   Translated: {report['summary']['translated']}")
    print(f"   Not Translated: {report['summary']['not_translated']}")
    print(f"   Coverage: {report['summary']['coverage_percent']}%")
    
    return report
