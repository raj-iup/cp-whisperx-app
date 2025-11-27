#!/usr/bin/env python3
"""
beam_search_comparison.py - Compare translation quality across different beam search widths

Generates multiple translations with beam sizes 4-10 for manual quality inspection.
Creates side-by-side comparison outputs for determining optimal beam width.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime


def translate_with_beam_width(
    segments_file: Path,
    beam_width: int,
    output_dir: Path,
    source_lang: str,
    target_lang: str,
    device: str = "mps",
    translator_script: Path = None,
    logger: logging.Logger = None
) -> Dict[str, Any]:
    """
    Translate segments with specific beam width
    
    Returns:
        Dict with translation results and timing
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    import time
    import sys
    
    output_file = output_dir / f"segments_{target_lang}_beam{beam_width}.json"
    
    logger.info(f"▶ Beam width {beam_width}: Starting translation...")
    
    start_time = time.time()
    
    try:
        # Add indictrans2 script directory to path
        script_dir = translator_script.parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        
        # Import the translator
        from indictrans2_translator import IndicTrans2Translator, TranslationConfig
        
        # Load input segments
        with open(segments_file) as f:
            data = json.load(f)
        
        segments = data.get("segments", [])
        
        if not segments:
            raise ValueError("No segments found in input file")
        
        # Create translator with specific beam width
        config = TranslationConfig(
            device=device,
            num_beams=beam_width
        )
        
        translator = IndicTrans2Translator(config=config)
        
        # Translate segments
        translated_segments = translator.translate_segments(
            segments,
            skip_english=True
        )
        
        # Save output
        output_data = {
            "segments": translated_segments,
            "language": target_lang,
            "source_language": source_lang
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        elapsed = time.time() - start_time
        
        logger.info(f"✓ Beam width {beam_width}: Completed in {elapsed:.1f}s ({len(translated_segments)} segments)")
        
        return {
            "beam_width": beam_width,
            "elapsed_time": elapsed,
            "num_segments": len(translated_segments),
            "output_file": str(output_file),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"✗ Beam width {beam_width}: Failed - {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return {
            "beam_width": beam_width,
            "success": False,
            "error": str(e)
        }


def generate_comparison_report(
    results: List[Dict[str, Any]],
    output_dir: Path,
    logger: logging.Logger = None
) -> Path:
    """
    Generate side-by-side comparison report
    
    Returns:
        Path to HTML comparison report
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    report_file = output_dir / "beam_comparison_report.html"
    
    # Load all translations
    translations = {}
    for result in results:
        if not result["success"]:
            continue
        
        beam_width = result["beam_width"]
        with open(result["output_file"]) as f:
            data = json.load(f)
        translations[beam_width] = data.get("segments", [])
    
    # Generate HTML report
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Beam Search Comparison Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .summary {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary table {
            width: 100%;
            border-collapse: collapse;
        }
        .summary th, .summary td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .summary th {
            background: #4CAF50;
            color: white;
        }
        .segment {
            background: white;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .segment-header {
            background: #2196F3;
            color: white;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
            font-weight: bold;
        }
        .original {
            background: #e3f2fd;
            padding: 10px;
            border-left: 4px solid #2196F3;
            margin-bottom: 10px;
            font-style: italic;
        }
        .translation {
            padding: 10px;
            border-left: 4px solid #4CAF50;
            margin-bottom: 5px;
        }
        .beam-label {
            font-weight: bold;
            color: #4CAF50;
            display: inline-block;
            min-width: 80px;
        }
        .diff {
            background: #fff9c4;
        }
        .navigation {
            position: fixed;
            right: 20px;
            top: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        .navigation a {
            display: block;
            color: #2196F3;
            text-decoration: none;
            padding: 5px 0;
        }
        .navigation a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
"""
    
    # Add header
    html += f"""
    <h1>🔍 Beam Search Comparison Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
    
    # Add summary table
    html += """
    <div class="summary">
        <h2>Summary Statistics</h2>
        <table>
            <tr>
                <th>Beam Width</th>
                <th>Translation Time</th>
                <th>Segments</th>
                <th>Output File</th>
            </tr>
"""
    
    for result in results:
        if not result["success"]:
            continue
        html += f"""
            <tr>
                <td><strong>Beam {result['beam_width']}</strong></td>
                <td>{result['elapsed_time']:.1f}s</td>
                <td>{result['num_segments']}</td>
                <td><code>{Path(result['output_file']).name}</code></td>
            </tr>
"""
    
    html += """
        </table>
        <p><strong>Note:</strong> Higher beam widths typically produce better quality but take longer.</p>
    </div>
"""
    
    # Add navigation
    html += """
    <div class="navigation">
        <strong>Quick Navigation</strong>
"""
    for i in range(min(10, len(list(translations.values())[0]) if translations else 0)):
        html += f'        <a href="#seg{i}">Segment {i+1}</a>\n'
    html += """
    </div>
"""
    
    # Add segment comparisons
    if translations:
        beam_widths = sorted(translations.keys())
        num_segments = len(translations[beam_widths[0]])
        
        for i in range(num_segments):
            html += f"""
    <div class="segment" id="seg{i}">
        <div class="segment-header">Segment {i+1} / {num_segments}</div>
"""
            
            # Original text
            first_seg = translations[beam_widths[0]][i]
            html += f"""
        <div class="original">
            <strong>Original:</strong> {first_seg.get('text', 'N/A')}
        </div>
"""
            
            # Translations for each beam width
            for beam in beam_widths:
                seg = translations[beam][i]
                translated = seg.get('translated_text', seg.get('text', 'N/A'))
                
                html += f"""
        <div class="translation">
            <span class="beam-label">Beam {beam}:</span> {translated}
        </div>
"""
            
            html += """
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    # Save report
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info(f"✓ Comparison report generated: {report_file}")
    
    return report_file


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Compare translation quality across different beam search widths"
    )
    parser.add_argument("segments", type=Path, help="Input segments JSON")
    parser.add_argument("output_dir", type=Path, help="Output directory for comparisons")
    parser.add_argument("--source-lang", default="hi", help="Source language")
    parser.add_argument("--target-lang", default="en", help="Target language")
    parser.add_argument("--beam-range", default="4,10", 
                       help="Beam width range (min,max), e.g., '4,10'")
    parser.add_argument("--device", default="mps", help="Device: mps, cuda, cpu")
    parser.add_argument("--translator", type=Path,
                       help="Path to translator script (defaults to scripts/indictrans2_translator.py)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='[%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Verify inputs
    if not args.segments.exists():
        logger.error(f"Segments file not found: {args.segments}")
        sys.exit(1)
    
    # Default translator path
    if args.translator is None:
        script_dir = Path(__file__).parent
        args.translator = script_dir / "indictrans2_translator.py"
    
    if not args.translator.exists():
        logger.error(f"Translator script not found: {args.translator}")
        sys.exit(1)
    
    # Parse beam range
    try:
        min_beam, max_beam = map(int, args.beam_range.split(','))
        if not (1 <= min_beam <= max_beam <= 10):
            raise ValueError("Beam range must be between 1-10")
    except:
        logger.error(f"Invalid beam range: {args.beam_range}")
        logger.error("Expected format: 'min,max' (e.g., '4,10')")
        sys.exit(1)
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("BEAM SEARCH COMPARISON ANALYSIS")
    logger.info("=" * 80)
    logger.info(f"Input: {args.segments}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Translation: {args.source_lang} → {args.target_lang}")
    logger.info(f"Beam range: {min_beam} to {max_beam}")
    logger.info(f"Device: {args.device}")
    logger.info("=" * 80)
    logger.info("")
    
    # Run translations with different beam widths
    results = []
    for beam_width in range(min_beam, max_beam + 1):
        result = translate_with_beam_width(
            args.segments,
            beam_width,
            args.output_dir,
            args.source_lang,
            args.target_lang,
            args.device,
            args.translator,
            logger
        )
        results.append(result)
        logger.info("")
    
    # Generate comparison report
    logger.info("=" * 80)
    logger.info("Generating comparison report...")
    report_file = generate_comparison_report(results, args.output_dir, logger)
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("COMPARISON COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Report: {report_file}")
    logger.info(f"Open in browser: open {report_file}")
    logger.info("")
    logger.info("Translation outputs:")
    for result in results:
        if result["success"]:
            logger.info(f"  • Beam {result['beam_width']}: {result['output_file']}")
    logger.info("=" * 80)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
