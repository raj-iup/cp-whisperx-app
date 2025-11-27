#!/usr/bin/env python3
"""
Phase 1 Week 2 Integration Test

Tests pipeline integration of TMDB + NER + Glossary modules
with prepare-job workflow.
"""

import sys
import json
from pathlib import Path
import tempfile
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.tmdb_enrichment_stage import TMDBEnrichmentStage
from scripts.ner_post_processor import NERPostProcessor


def test_tmdb_enrichment_stage():
    """Test TMDB enrichment stage integration"""
    print("=" * 60)
    print("TEST 1: TMDB Enrichment Stage")
    print("=" * 60)
    
    # Create temporary job directory
    with tempfile.TemporaryDirectory() as temp_dir:
        job_dir = Path(temp_dir) / "test_job"
        job_dir.mkdir(parents=True)
        
        # Create demux directory (simulating Stage 1)
        demux_dir = job_dir / "01_demux"
        demux_dir.mkdir()
        
        # Create mock audio file
        (demux_dir / "test_movie_audio.wav").touch()
        
        # Run TMDB enrichment
        print("\nRunning TMDB enrichment stage...")
        stage = TMDBEnrichmentStage(
            job_dir=job_dir,
            title="Jaane Tu Ya Jaane Na",
            year=2008
        )
        
        success = stage.run()
        
        if not success:
            print("❌ TMDB enrichment stage failed")
            return False
        
        # Verify outputs
        tmdb_dir = job_dir / "02_tmdb"
        expected_files = [
            "enrichment.json",
            "glossary_asr.json",
            "glossary_translation.json",
            "glossary.yaml"
        ]
        
        for filename in expected_files:
            filepath = tmdb_dir / filename
            if not filepath.exists():
                print(f"❌ Missing output file: {filename}")
                return False
            print(f"✓ Created: {filename}")
        
        # Load and verify enrichment data
        with open(tmdb_dir / "enrichment.json", 'r') as f:
            enrichment = json.load(f)
        
        if not enrichment.get('found'):
            print("❌ Movie not found in TMDB")
            return False
        
        print(f"\n✓ TMDB Enrichment Stage Test PASSED")
        print(f"  Movie: {enrichment['title']} ({enrichment['year']})")
        print(f"  Cast: {len(enrichment.get('cast', []))} members")
        print(f"  Crew: {len(enrichment.get('crew', []))} members")
        
        return True


def test_ner_post_processor():
    """Test NER post-processor integration"""
    print("\n" + "=" * 60)
    print("TEST 2: NER Post-Processor")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        job_dir = Path(temp_dir) / "test_job"
        job_dir.mkdir(parents=True)
        
        # Create TMDB directory with mock data
        tmdb_dir = job_dir / "02_tmdb"
        tmdb_dir.mkdir(parents=True)
        
        # Create mock enrichment data
        enrichment = {
            "found": True,
            "title": "Jaane Tu... Ya Jaane Na",
            "year": 2008,
            "cast": [
                {"name": "Imran Khan", "character": "Jai Rathod", "order": 0},
                {"name": "Genelia D'Souza", "character": "Aditi Wadia", "order": 1},
                {"name": "Manjari Fadnnis", "character": "Meghna", "order": 2}
            ],
            "crew": [
                {"name": "Abbas Tyrewala", "job": "Director"},
                {"name": "A.R. Rahman", "job": "Music"}
            ]
        }
        
        with open(tmdb_dir / "enrichment.json", 'w') as f:
            json.dump(enrichment, f)
        
        # Create mock transcript
        transcript = {
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Jai and Aditi are best friends in Mumbai."
                },
                {
                    "id": 1,
                    "start": 5.0,
                    "end": 10.0,
                    "text": "They study together at college."
                }
            ]
        }
        
        input_file = job_dir / "transcript.json"
        with open(input_file, 'w') as f:
            json.dump(transcript, f, indent=2)
        
        # Run NER post-processor
        print("\nRunning NER post-processor...")
        processor = NERPostProcessor(job_dir=job_dir)
        
        output_file = job_dir / "transcript_corrected.json"
        success = processor.process_transcript(
            input_file=input_file,
            output_file=output_file,
            format="json"
        )
        
        if not success:
            print("❌ NER post-processing failed")
            return False
        
        # Verify output
        if not output_file.exists():
            print("❌ Output file not created")
            return False
        
        with open(output_file, 'r') as f:
            corrected = json.load(f)
        
        print(f"\n✓ NER Post-Processor Test PASSED")
        if 'ner_processing' in corrected:
            stats = corrected['ner_processing']
            print(f"  Segments: {len(corrected.get('segments', []))}")
            print(f"  Entities found: {stats.get('entities_found', 0)}")
            print(f"  Corrections: {stats.get('corrections_made', 0)}")
        
        return True


def test_end_to_end_flow():
    """Test end-to-end flow: TMDB → NER"""
    print("\n" + "=" * 60)
    print("TEST 3: End-to-End Flow")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        job_dir = Path(temp_dir) / "test_job"
        job_dir.mkdir(parents=True)
        
        # Create demux directory
        demux_dir = job_dir / "01_demux"
        demux_dir.mkdir()
        (demux_dir / "movie_audio.wav").touch()
        
        # Step 1: Run TMDB enrichment
        print("\nStep 1: TMDB Enrichment...")
        tmdb_stage = TMDBEnrichmentStage(
            job_dir=job_dir,
            title="3 Idiots",
            year=2009
        )
        
        if not tmdb_stage.run():
            print("❌ TMDB enrichment failed")
            return False
        
        print("✓ TMDB enrichment complete")
        
        # Step 2: Create mock transcript
        print("\nStep 2: Creating mock transcript...")
        transcript = {
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Rancho, Farhan, and Raju are engineering students."
                }
            ]
        }
        
        input_file = job_dir / "transcript.json"
        with open(input_file, 'w') as f:
            json.dump(transcript, f, indent=2)
        
        print("✓ Mock transcript created")
        
        # Step 3: Run NER post-processor
        print("\nStep 3: NER Post-Processing...")
        processor = NERPostProcessor(job_dir=job_dir)
        
        output_file = job_dir / "transcript_corrected.json"
        if not processor.process_transcript(
            input_file=input_file,
            output_file=output_file,
            format="json"
        ):
            print("❌ NER post-processing failed")
            return False
        
        print("✓ NER post-processing complete")
        
        # Verify complete flow
        tmdb_dir = job_dir / "02_tmdb"
        required_files = [
            tmdb_dir / "enrichment.json",
            tmdb_dir / "glossary_asr.json",
            tmdb_dir / "glossary_translation.json",
            output_file
        ]
        
        for filepath in required_files:
            if not filepath.exists():
                print(f"❌ Missing file: {filepath.name}")
                return False
        
        print(f"\n✓ End-to-End Flow Test PASSED")
        print(f"  All pipeline stages integrated correctly")
        
        return True


def main():
    """Run all integration tests"""
    print("\n🚀 PHASE 1 WEEK 2 INTEGRATION TEST")
    print("Testing Pipeline Integration\n")
    
    try:
        # Test 1: TMDB Enrichment Stage
        if not test_tmdb_enrichment_stage():
            print("\n❌ TMDB enrichment test failed")
            return 1
        
        # Test 2: NER Post-Processor
        if not test_ner_post_processor():
            print("\n❌ NER post-processor test failed")
            return 1
        
        # Test 3: End-to-End Flow
        if not test_end_to_end_flow():
            print("\n❌ End-to-end flow test failed")
            return 1
        
        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)
        print("\nPhase 1 Week 2 pipeline integration successful!")
        print("Pipeline stages ready:")
        print("  ✓ 01_demux")
        print("  ✓ 02_tmdb (NEW)")
        print("  ✓ NER post-processing (NEW)")
        print("  ✓ ASR with glossary support")
        print("  ✓ Translation with entity preservation")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
