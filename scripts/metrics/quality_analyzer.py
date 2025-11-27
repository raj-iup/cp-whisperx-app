#!/usr/bin/env python3
"""
Quality Metrics Analyzer for CP-WhisperX-App

Purpose: Analyze transcription and translation quality
Input: Segment JSON files from ASR and translation stages
Output: Quality metrics report (JSON)
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter
import re

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger


class QualityAnalyzer:
    """Analyze transcription and translation quality."""
    
    def __init__(self, job_dir: Path, logger: Optional[PipelineLogger] = None):
        """Initialize quality analyzer.
        
        Args:
            job_dir: Job output directory
            logger: Optional logger instance
        """
        self.job_dir = Path(job_dir)
        self.logger = logger or PipelineLogger("quality_analyzer")
    
    def analyze_transcription(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate transcription quality metrics.
        
        Args:
            segments: List of transcription segments
            
        Returns:
            Dictionary of quality metrics
        """
        if not segments:
            return {"error": "No segments provided"}
        
        metrics = {
            "total_segments": len(segments),
            "total_duration": self._calculate_duration(segments),
            "confidence_distribution": self._analyze_confidence(segments),
            "text_statistics": self._analyze_text(segments),
            "low_confidence_count": self._count_low_confidence(segments),
            "hallucination_indicators": self._detect_hallucination_patterns(segments),
        }
        
        return metrics
    
    def analyze_translation(
        self, 
        source: List[Dict[str, Any]], 
        translated: List[Dict[str, Any]],
        glossary: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Calculate translation quality metrics.
        
        Args:
            source: Source language segments
            translated: Translated segments
            glossary: Optional glossary terms
            
        Returns:
            Dictionary of quality metrics
        """
        if not translated:
            return {"error": "No translated segments provided"}
        
        metrics = {
            "total_segments": len(translated),
            "untranslated_count": self._count_untranslated(translated),
            "untranslated_segments": self._find_untranslated_segments(translated),
            "translation_coverage": self._calculate_coverage(source, translated),
        }
        
        if glossary:
            metrics["glossary_metrics"] = self._analyze_glossary_usage(
                translated, glossary
            )
        
        return metrics
    
    def _calculate_duration(self, segments: List[Dict[str, Any]]) -> float:
        """Calculate total duration of segments."""
        if not segments:
            return 0.0
        
        total = 0.0
        for seg in segments:
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            total += (end - start)
        
        return round(total, 2)
    
    def _analyze_confidence(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze confidence score distribution."""
        confidences = []
        
        for seg in segments:
            # Try different confidence field names
            conf = seg.get('confidence') or seg.get('avg_logprob') or seg.get('score')
            if conf is not None:
                confidences.append(float(conf))
        
        if not confidences:
            return {
                "available": False,
                "note": "No confidence scores found in segments"
            }
        
        # Calculate distribution
        return {
            "available": True,
            "count": len(confidences),
            "min": round(min(confidences), 3),
            "max": round(max(confidences), 3),
            "mean": round(sum(confidences) / len(confidences), 3),
            "low_confidence_threshold": 0.6,
            "below_threshold": sum(1 for c in confidences if c < 0.6),
        }
    
    def _analyze_text(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze text content statistics."""
        all_text = " ".join(seg.get('text', '') for seg in segments)
        words = all_text.split()
        
        return {
            "total_characters": len(all_text),
            "total_words": len(words),
            "avg_segment_length": round(len(all_text) / len(segments), 1) if segments else 0,
            "avg_words_per_segment": round(len(words) / len(segments), 1) if segments else 0,
        }
    
    def _count_low_confidence(
        self, 
        segments: List[Dict[str, Any]], 
        threshold: float = 0.6
    ) -> int:
        """Count segments with low confidence."""
        count = 0
        
        for seg in segments:
            conf = seg.get('confidence') or seg.get('avg_logprob') or seg.get('score')
            if conf is not None and float(conf) < threshold:
                count += 1
        
        return count
    
    def _detect_hallucination_patterns(
        self, 
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detect potential hallucination patterns."""
        texts = [seg.get('text', '') for seg in segments]
        
        # Check for repetitions
        repetition_count = 0
        for i in range(len(texts) - 1):
            if texts[i] and texts[i] == texts[i + 1]:
                repetition_count += 1
        
        # Check for very short segments (possible noise)
        short_segments = sum(1 for t in texts if len(t.strip()) <= 3)
        
        # Check for common hallucination phrases
        hallucination_phrases = [
            "प्रश्न प्रश्न", "thank you", "thanks for watching",
            "subscribe", "like and subscribe"
        ]
        
        phrase_count = 0
        for text in texts:
            for phrase in hallucination_phrases:
                if phrase.lower() in text.lower():
                    phrase_count += 1
                    break
        
        return {
            "consecutive_repetitions": repetition_count,
            "short_segments": short_segments,
            "potential_hallucination_phrases": phrase_count,
            "repetition_rate": round(repetition_count / len(segments), 3) if segments else 0,
        }
    
    def _count_untranslated(self, translated: List[Dict[str, Any]]) -> int:
        """Count segments with untranslated text."""
        count = 0
        
        # Devanagari Unicode range
        devanagari_pattern = re.compile(r'[\u0900-\u097F]')
        
        for seg in translated:
            text = seg.get('text', '')
            if devanagari_pattern.search(text):
                count += 1
        
        return count
    
    def _find_untranslated_segments(
        self, 
        translated: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find segments with untranslated text."""
        untranslated = []
        devanagari_pattern = re.compile(r'[\u0900-\u097F]')
        
        for i, seg in enumerate(translated):
            text = seg.get('text', '')
            if devanagari_pattern.search(text):
                untranslated.append({
                    "segment_index": i,
                    "start": seg.get('start'),
                    "end": seg.get('end'),
                    "text": text,
                })
        
        return untranslated[:10]  # Limit to first 10 for brevity
    
    def _calculate_coverage(
        self, 
        source: List[Dict[str, Any]], 
        translated: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate translation coverage."""
        source_count = len(source)
        translated_count = len(translated)
        
        coverage = (translated_count / source_count * 100) if source_count > 0 else 0
        
        return {
            "source_segments": source_count,
            "translated_segments": translated_count,
            "coverage_percentage": round(coverage, 1),
        }
    
    def _analyze_glossary_usage(
        self, 
        translated: List[Dict[str, Any]], 
        glossary: Dict[str, str]
    ) -> Dict[str, Any]:
        """Analyze glossary term usage in translation."""
        all_text = " ".join(seg.get('text', '').lower() for seg in translated)
        
        hits = 0
        hit_terms = []
        
        for source_term, target_term in glossary.items():
            # Check if target term appears in translation
            if target_term.lower() in all_text:
                hits += 1
                hit_terms.append(target_term)
        
        hit_rate = (hits / len(glossary) * 100) if glossary else 0
        
        return {
            "total_glossary_terms": len(glossary),
            "terms_found": hits,
            "hit_rate_percentage": round(hit_rate, 1),
            "sample_hits": hit_terms[:10],  # First 10 for brevity
        }
    
    def generate_report(
        self,
        transcription_metrics: Optional[Dict[str, Any]] = None,
        translation_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive quality report.
        
        Args:
            transcription_metrics: Transcription quality metrics
            translation_metrics: Translation quality metrics
            
        Returns:
            Complete quality report
        """
        from datetime import datetime
        
        report = {
            "job_id": self.job_dir.name,
            "job_path": str(self.job_dir),
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
        }
        
        if transcription_metrics:
            report["transcription"] = transcription_metrics
        
        if translation_metrics:
            report["translation"] = translation_metrics
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = "quality_report.json") -> Path:
        """Save quality report to file.
        
        Args:
            report: Quality report dictionary
            filename: Output filename
            
        Returns:
            Path to saved report
        """
        report_path = self.job_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✓ Quality report saved: {filename}")
        
        return report_path
    
    def generate_summary_text(self, report: Dict[str, Any]) -> str:
        """Generate human-readable summary from report.
        
        Args:
            report: Quality report dictionary
            
        Returns:
            Formatted summary text
        """
        lines = []
        lines.append("=" * 80)
        lines.append("QUALITY METRICS SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Job: {report.get('job_id', 'N/A')}")
        lines.append(f"Generated: {report.get('timestamp', 'N/A')}")
        lines.append("")
        
        # Transcription metrics
        if "transcription" in report:
            trans = report["transcription"]
            lines.append("TRANSCRIPTION QUALITY")
            lines.append("-" * 80)
            lines.append(f"Total Segments: {trans.get('total_segments', 0)}")
            lines.append(f"Total Duration: {trans.get('total_duration', 0):.1f}s")
            
            if "confidence_distribution" in trans:
                conf = trans["confidence_distribution"]
                if conf.get("available"):
                    lines.append(f"Confidence Range: {conf.get('min', 0):.3f} - {conf.get('max', 0):.3f}")
                    lines.append(f"Mean Confidence: {conf.get('mean', 0):.3f}")
                    lines.append(f"Low Confidence Count: {conf.get('below_threshold', 0)}")
            
            if "hallucination_indicators" in trans:
                hall = trans["hallucination_indicators"]
                lines.append(f"Repetition Rate: {hall.get('repetition_rate', 0):.1%}")
                lines.append(f"Potential Hallucinations: {hall.get('potential_hallucination_phrases', 0)}")
            
            lines.append("")
        
        # Translation metrics
        if "translation" in report:
            transl = report["translation"]
            lines.append("TRANSLATION QUALITY")
            lines.append("-" * 80)
            lines.append(f"Translated Segments: {transl.get('total_segments', 0)}")
            lines.append(f"Untranslated Text Count: {transl.get('untranslated_count', 0)}")
            
            if "glossary_metrics" in transl:
                gloss = transl["glossary_metrics"]
                lines.append(f"Glossary Hit Rate: {gloss.get('hit_rate_percentage', 0):.1f}%")
            
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


def main():
    """Command-line interface for quality analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze transcription/translation quality")
    parser.add_argument("job_dir", type=Path, help="Job directory path")
    parser.add_argument("--transcription", type=Path, help="Transcription segments JSON")
    parser.add_argument("--translation", type=Path, help="Translation segments JSON")
    parser.add_argument("--glossary", type=Path, help="Glossary JSON")
    parser.add_argument("--output", default="quality_report.json", help="Output filename")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = QualityAnalyzer(args.job_dir)
    
    transcription_metrics = None
    translation_metrics = None
    
    # Analyze transcription
    if args.transcription and args.transcription.exists():
        with open(args.transcription, 'r', encoding='utf-8') as f:
            data = json.load(f)
            segments = data.get('segments', [])
            transcription_metrics = analyzer.analyze_transcription(segments)
            print(f"✓ Analyzed {len(segments)} transcription segments")
    
    # Analyze translation
    if args.translation and args.translation.exists():
        with open(args.translation, 'r', encoding='utf-8') as f:
            data = json.load(f)
            translated = data.get('segments', [])
        
        source = []
        if args.transcription and args.transcription.exists():
            with open(args.transcription, 'r', encoding='utf-8') as f:
                data = json.load(f)
                source = data.get('segments', [])
        
        glossary = None
        if args.glossary and args.glossary.exists():
            with open(args.glossary, 'r', encoding='utf-8') as f:
                glossary = json.load(f)
        
        translation_metrics = analyzer.analyze_translation(source, translated, glossary)
        print(f"✓ Analyzed {len(translated)} translated segments")
    
    # Generate report
    report = analyzer.generate_report(transcription_metrics, translation_metrics)
    
    # Save report
    report_path = analyzer.save_report(report, args.output)
    print(f"✓ Report saved: {report_path}")
    
    # Generate summary
    summary = analyzer.generate_summary_text(report)
    summary_path = args.job_dir / "quality_summary.txt"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"✓ Summary saved: {summary_path}")
    
    # Print summary
    print("\n" + summary)


if __name__ == "__main__":
    main()
