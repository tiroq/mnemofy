#!/usr/bin/env python3
"""
Performance benchmark for mnemofy key operations.

Validates:
- Heuristic classification: <100ms (SC-006)
- Menu rendering: <200ms latency (SC-009)
"""

import time
from pathlib import Path

def benchmark_heuristic_classification():
    """Benchmark heuristic meeting type detection."""
    from mnemofy.classifier import HeuristicClassifier
    
    # Load sample transcript
    sample_path = Path(__file__).parent.parent / "examples" / "planning-meeting-example.txt"
    if not sample_path.exists():
        print(f"⚠️  Sample file not found: {sample_path}")
        return None
    
    transcript_text = sample_path.read_text()
    
    # Convert to segment format (simulate typical segments)
    lines = [line.strip() for line in transcript_text.split('\n') if line.strip()]
    segments = []
    for i, line in enumerate(lines):
        if line.startswith('[') and ']' in line:
            # Parse timestamp and text
            timestamp_part, text = line.split(']', 1)
            text = text.strip()
            segments.append({
                'start': i * 10.0,
                'end': (i + 1) * 10.0,
                'text': text
            })
    
    classifier = HeuristicClassifier()
    
    # Warmup
    classifier.detect_meeting_type(transcript_text, segments)
    
    # Benchmark
    times = []
    for _ in range(10):
        start = time.time()
        result = classifier.detect_meeting_type(transcript_text, segments)
        duration = time.time() - start
        times.append(duration * 1000)  # Convert to ms
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    
    status = "✅ PASS" if avg_time < 100 else "❌ FAIL"
    threshold_status = "✅ PASS" if max_time < 100 else "❌ FAIL"
    
    print("\n" + "="*60)
    print("BENCHMARK: Heuristic Classification")
    print("="*60)
    print(f"Requirement: <100ms (SC-006)")
    print(f"Samples: {len(times)}")
    print(f"Average: {avg_time:.1f}ms {status}")
    print(f"Min: {min_time:.1f}ms")
    print(f"Max: {max_time:.1f}ms {threshold_status}")
    print(f"Detected: {result.detected_type.value} (confidence: {result.confidence:.2f})")
    
    return avg_time < 100 and max_time < 100


def benchmark_menu_rendering():
    """Benchmark meeting type menu initialization."""
    from mnemofy.tui.meeting_type_menu import MeetingTypeMenu
    from mnemofy.classifier import ClassificationResult, MeetingType
    from datetime import datetime
    
    # Create classification result
    result = ClassificationResult(
        detected_type=MeetingType.PLANNING,
        confidence=0.75,
        evidence=["scope", "timeline", "estimate", "Q2", "milestone"],
        secondary_types=[
            (MeetingType.STATUS, 0.48),
            (MeetingType.DESIGN, 0.31),
            (MeetingType.DEMO, 0.22),
            (MeetingType.TALK, 0.15),
        ],
        engine="heuristic",
        timestamp=datetime.now()
    )
    
    # Benchmark menu creation and initialization
    times = []
    for _ in range(10):
        start = time.time()
        menu = MeetingTypeMenu(result)
        # Force computation of all candidates and descriptions
        for mt, score in menu.candidates:
            _ = menu._get_type_description(mt)
            _ = menu._get_confidence_color(score)
        duration = time.time() - start
        times.append(duration * 1000)  # Convert to ms
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    
    status = "✅ PASS" if avg_time < 200 else "❌ FAIL"
    threshold_status = "✅ PASS" if max_time < 200 else "❌ FAIL"
    
    print("\n" + "="*60)
    print("BENCHMARK: Meeting Type Menu Initialization")
    print("="*60)
    print(f"Requirement: <200ms latency (SC-009)")
    print(f"Samples: {len(times)}")
    print(f"Average: {avg_time:.1f}ms {status}")
    print(f"Min: {min_time:.1f}ms")
    print(f"Max: {max_time:.1f}ms {threshold_status}")
    print(f"Note: User interaction time not measured (requires TTY)")
    
    return avg_time < 200 and max_time < 200


def benchmark_normalization():
    """Benchmark transcript normalization."""
    from mnemofy.transcriber import Transcriber
    
    # Create sample transcription with typical issues (segments format)
    sample_segments = []
    segment_texts = [
        "So um, I think we should like, you know, uh, probably consider the the the database migration.",
        "Um, we could you know use PostgreSQL right?",
        "And uh, like we need to to to think about the, um, performance implications.",
        "We discussed in the the meeting.",
        "You know, it's it's gonna be tough.",
    ] * 2  # Repeat for realistic length
    
    for i, text in enumerate(segment_texts):
        sample_segments.append({
            "id": i,
            "start": i * 5.0,
            "end": (i + 1) * 5.0,
            "text": text
        })
    
    transcription = {
        "text": " ".join(segment_texts),
        "segments": sample_segments
    }
    
    transcriber = Transcriber(model_name="base")
    
    # Warmup
    transcriber.normalize_transcript(transcription, remove_fillers=True)
    
    # Benchmark
    times = []
    change_counts = []
    for _ in range(10):
        # Re-create transcription for each run (to avoid already-normalized data)
        test_transcription = {
            "text": transcription["text"],
            "segments": [seg.copy() for seg in sample_segments]
        }
        
        start = time.time()
        result = transcriber.normalize_transcript(test_transcription, remove_fillers=True)
        duration = time.time() - start
        times.append(duration * 1000)  # Convert to ms
        change_counts.append(len(result.changes))
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    avg_changes = sum(change_counts) / len(change_counts)
    total_chars = len(transcription["text"])
    
    print("\n" + "="*60)
    print("BENCHMARK: Transcript Normalization")
    print("="*60)
    print(f"Input: {len(sample_segments)} segments, {total_chars} chars")
    print(f"Samples: {len(times)}")
    print(f"Average: {avg_time:.1f}ms")
    print(f"Min: {min_time:.1f}ms")
    print(f"Max: {max_time:.1f}ms")
    print(f"Avg changes: {avg_changes:.0f}")
    if avg_time > 0:
        print(f"Throughput: {total_chars / (avg_time/1000):.0f} chars/sec")
    
    return True


def main():
    """Run all benchmarks."""
    print("mnemofy Performance Benchmarks")
    print("="*60)
    
    results = {}
    
    # Run benchmarks
    results['classification'] = benchmark_heuristic_classification()
    results['menu'] = benchmark_menu_rendering()
    results['normalization'] = benchmark_normalization()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_passed = all(r for r in results.values() if r is not None)
    
    for name, passed in results.items():
        if passed is None:
            status = "⚠️  SKIP"
        elif passed:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        print(f"{name.title():20s} {status}")
    
    print("="*60)
    if all_passed:
        print("✅ All benchmarks PASSED")
        return 0
    else:
        print("❌ Some benchmarks FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
