import json
import datetime
import csv
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

def generate_translation_report(english_texts: List[str], japanese_texts: List[str], 
                              ignored_words: List[str], url: str) -> Dict[str, Any]:
    """Generate focused translation report with proper text matching"""
    
    # Clean and filter texts
    english_clean = [text for text in english_texts if text and len(text.strip()) > 2 and len(text.strip()) < 100]
    japanese_clean = [text for text in japanese_texts if text and len(text.strip()) > 2 and len(text.strip()) < 100]
    
    # Analyze translations with proper matching
    not_translated = []
    translated = []
    ignored = []
    
    # Create proper text pairs by position (assuming same order from same page)
    text_pairs = []
    
    # Use position-based matching for better accuracy
    max_len = max(len(english_clean), len(japanese_clean))
    for i in range(max_len):
        en_text = english_clean[i] if i < len(english_clean) else ""
        jp_text = japanese_clean[i] if i < len(japanese_clean) else ""
        
        if en_text and jp_text:
            text_pairs.append({"english": en_text, "japanese": jp_text})
        elif en_text:
            text_pairs.append({"english": en_text, "japanese": ""})
        elif jp_text:
            text_pairs.append({"english": "", "japanese": jp_text})
    
    # Analyze each pair
    for pair in text_pairs:
        en_text = pair["english"]
        jp_text = pair["japanese"]
        
        # Skip if text is in ignored words
        if any(ignored_word.lower() in en_text.lower() for ignored_word in ignored_words):
            ignored.append(pair)
            continue
        
        # Check if Japanese text contains actual Japanese characters
        japanese_chars = sum(1 for char in jp_text if '\u3040' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FFF')
        japanese_ratio = japanese_chars / len(jp_text) if jp_text else 0
        
        if japanese_ratio > 0.3:  # At least 30% Japanese characters
            translated.append(pair)
        else:
            not_translated.append(pair)
    
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
            "translated": translated[:20],  # Limit to top 20 translated
            "not_translated": not_translated[:20],  # Limit to top 20 untranslated
            "ignored": ignored[:10]  # Limit to top 10 ignored
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
    """Save report as CSV with proper UTF-8 BOM for Excel compatibility"""
    Path("reports").mkdir(exist_ok=True)
    filepath = Path("reports") / filename
    
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(["Type", "English Text", "Japanese Text", "Length", "Status"])
        
        # Write translated texts
        for item in report["details"]["translated"]:
            writer.writerow(["Translated", item["english"], item["japanese"], len(item["english"]), "✅"])
        
        # Write not translated texts
        for item in report["details"]["not_translated"]:
            writer.writerow(["Not Translated", item["english"], item["japanese"], len(item["english"]), "❌"])
        
        # Write ignored texts
        for item in report["details"]["ignored"]:
            writer.writerow(["Ignored", item["english"], item["japanese"], len(item["english"]), "⚠️"])
    
    print(f"📋 CSV report saved: {filepath}")
    return filepath

def save_untranslated_words_report(report: Dict[str, Any], filename: str = "untranslated_words.csv"):
    """Save focused report of untranslated words for translation team"""
    Path("reports").mkdir(exist_ok=True)
    filepath = Path("reports") / filename
    
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(["English Text", "Current Japanese Text", "Text Length", "Priority", "Category"])
        
        # Filter and sort untranslated texts
        untranslated = []
        for item in report["details"]["not_translated"]:
            en_text = item["english"]
            jp_text = item["japanese"]
            
            # Skip obvious non-translatable content
            if (len(en_text) < 3 or 
                en_text.isdigit() or 
                en_text in ['MB', 'KB', 'px', '2FA', 'API', 'VWO', 'Wingify'] or
                any(char.isdigit() for char in en_text) and len(en_text) < 5):
                continue
                
            untranslated.append(item)
        
        # Sort by length and importance
        untranslated.sort(key=lambda x: len(x["english"]), reverse=True)
        
        # Write top 15 most important untranslated texts
        for item in untranslated[:15]:
            en_text = item["english"]
            jp_text = item["japanese"]
            
            # Determine priority and category
            if len(en_text) > 20:
                priority = "High"
                category = "UI Labels"
            elif len(en_text) > 10:
                priority = "Medium"
                category = "Menu Items"
            else:
                priority = "Low"
                category = "Buttons"
            
            writer.writerow([en_text, jp_text, len(en_text), priority, category])
    
    print(f"📝 Focused untranslated words report saved: {filepath}")
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
    
    # Save detailed untranslated words report
    if report["details"]["not_translated"]:
        untranslated_file = save_untranslated_words_report(report)
    
    # Print summary
    print(f"\n🎯 Translation Report Summary:")
    print(f"   URL: {url}")
    print(f"   Total Texts: {report['summary']['total_texts']}")
    print(f"   Translated: {report['summary']['translated']}")
    print(f"   Not Translated: {report['summary']['not_translated']}")
    print(f"   Coverage: {report['summary']['coverage_percent']}%")
    
    return report
