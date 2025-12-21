#!/usr/bin/env python3
"""
Toggle Count Comparator
Compares toggle counts between signals by importing from vcd_toggle_counter.py
"""

import sys
from analysis import parse_vcd

try:
    import matplotlib.pyplot as plt
    import numpy as np
    PLOT_AVAILABLE = True
except ImportError:
    PLOT_AVAILABLE = False

def compare_signals(vcd_file, signal1, signal2, check_bits=False, do_plot=False):
    """
    Compare toggle counts between two signals.
    
    Args:
        vcd_file: Path to the VCD file
        signal1: First signal name (or pattern)
        signal2: Second signal name (or pattern)
        check_bits: If True, compare bit-wise toggles
        do_plot: If True, generate plots
        
    Returns:
        Comparison results dictionary
    """
    # Parse VCD file
    toggle_counts, all_signals, bit_toggle_counts = parse_vcd(vcd_file, track_bits=check_bits)
    
    # Find matching signals
    matches1 = [s for s in toggle_counts.keys() if signal1 in s]
    matches2 = [s for s in toggle_counts.keys() if signal2 in s]
    
    if not matches1:
        print(f"Error: No signal found matching '{signal1}'")
        return None
    if not matches2:
        print(f"Error: No signal found matching '{signal2}'")
        return None
    
    # Use first match if multiple found
    sig1 = matches1[0]
    sig2 = matches2[0]
    
    if len(matches1) > 1:
        print(f"Note: Multiple matches for '{signal1}', using '{sig1}'")
    if len(matches2) > 1:
        print(f"Note: Multiple matches for '{signal2}', using '{sig2}'")
    
    # Compare signal-level toggles
    count1 = toggle_counts.get(sig1, 0)
    count2 = toggle_counts.get(sig2, 0)
    
    # Calculate deviation metrics
    absolute_deviation = count1 - count2
    relative_deviation = (absolute_deviation / count2 * 100) if count2 != 0 else float('inf')
    mean_count = (count1 + count2) / 2
    std_deviation = ((count1 - mean_count)**2 + (count2 - mean_count)**2)**0.5
    
    results = {
        'sig1': sig1,
        'sig2': sig2,
        'count1': count1,
        'count2': count2,
        'absolute_deviation': absolute_deviation,
        'relative_deviation': relative_deviation,
        'mean': mean_count,
        'std_deviation': std_deviation,
        'bit_results': None
    }
    
    print("\n" + "=" * 70)
    print("SIGNAL-LEVEL TOGGLE COMPARISON")
    print("=" * 70)
    print(f"Signal 1: {sig1}")
    print(f"  Toggle count: {count1:,}")
    print(f"\nSignal 2: {sig2}")
    print(f"  Toggle count: {count2:,}")
    print("-" * 70)
    print(f"Deviation Metrics:")
    print(f"  Absolute deviation: {absolute_deviation:,}")
    print(f"  Relative deviation: {relative_deviation:.2f}%")
    print(f"  Mean toggle count: {mean_count:,.2f}")
    print(f"  Standard deviation: {std_deviation:,.2f}")
    print("-" * 70)
    
    if count1 == count2:
        print(f"✓ MATCH: Both signals have the same toggle count ({count1:,})")
    else:
        diff = abs(count1 - count2)
        percent_diff = (diff / max(count1, count2)) * 100 if max(count1, count2) > 0 else 0
        print(f"✗ MISMATCH: Toggle counts differ by {diff:,} ({percent_diff:.2f}%)")
        if count1 > count2:
            print(f"  '{sig1}' has {diff:,} more toggles")
        else:
            print(f"  '{sig2}' has {diff:,} more toggles")
    
    # Compare bit-level toggles if requested
    if check_bits and sig1 in bit_toggle_counts and sig2 in bit_toggle_counts:
        print("\n" + "=" * 70)
        print("BIT-LEVEL TOGGLE COMPARISON")
        print("=" * 70)
        
        bits1 = bit_toggle_counts[sig1]
        bits2 = bit_toggle_counts[sig2]
        
        all_bits = sorted(set(bits1.keys()) | set(bits2.keys()))
        
        matches = []
        mismatches = []
        bit_deviations = []
        
        print(f"\n{'Bit':<8} {sig1:<20} {sig2:<20} {'Deviation':<15} {'Status':<10}")
        print("-" * 80)
        
        for bit in all_bits:
            c1 = bits1.get(bit, 0)
            c2 = bits2.get(bit, 0)
            dev = c1 - c2
            bit_deviations.append(dev)
            
            if c1 == c2:
                status = "✓ MATCH"
                matches.append(bit)
            else:
                status = "✗ DIFFER"
                mismatches.append(bit)
            
            print(f"[{bit}]     {c1:<20,} {c2:<20,} {dev:<15,} {status}")
        
        # Calculate bit-level statistics
        bit_abs_devs = [abs(d) for d in bit_deviations]
        mean_bit_dev = sum(bit_deviations) / len(bit_deviations) if bit_deviations else 0
        mean_abs_dev = sum(bit_abs_devs) / len(bit_abs_devs) if bit_abs_devs else 0
        max_dev = max(bit_abs_devs) if bit_abs_devs else 0
        
        print("\n" + "-" * 80)
        print(f"Bit-level Statistics:")
        print(f"  Matching bits: {len(matches)}/{len(all_bits)}")
        print(f"  Differing bits: {len(mismatches)}/{len(all_bits)}")
        print(f"  Mean deviation: {mean_bit_dev:,.2f}")
        print(f"  Mean absolute deviation: {mean_abs_dev:,.2f}")
        print(f"  Maximum absolute deviation: {max_dev:,}")
        
        results['bit_results'] = {
            'bits': all_bits,
            'counts1': [bits1.get(b, 0) for b in all_bits],
            'counts2': [bits2.get(b, 0) for b in all_bits],
            'deviations': bit_deviations,
            'matches': matches,
            'mismatches': mismatches,
            'mean_deviation': mean_bit_dev,
            'mean_abs_deviation': mean_abs_dev,
            'max_deviation': max_dev
        }
    
    print("=" * 70)
    
    # Generate plots if requested
    if do_plot:
        plot_comparison(results, check_bits)
    
    return results

def plot_comparison(results, check_bits=False):
    """Plot comparison results and deviations."""
    if not PLOT_AVAILABLE:
        print("\nMatplotlib not available. Install with: pip install matplotlib")
        return
    
    sig1 = results['sig1']
    sig2 = results['sig2']
    
    # Plot 1: Signal-level comparison
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Bar chart comparing toggle counts
    ax1 = axes[0]
    signals = [sig1, sig2]
    counts = [results['count1'], results['count2']]
    colors = ['steelblue', 'coral']
    
    bars = ax1.bar(signals, counts, color=colors, edgecolor='black', alpha=0.7)
    ax1.set_ylabel('Toggle Count', fontsize=12)
    ax1.set_title('Signal Toggle Count Comparison', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{count:,}', ha='center', va='bottom', fontsize=10)
    
    # Deviation visualization
    ax2 = axes[1]
    metrics = ['Absolute\nDeviation', 'Std\nDeviation']
    values = [abs(results['absolute_deviation']), results['std_deviation']]
    
    bars = ax2.bar(metrics, values, color='crimson', edgecolor='black', alpha=0.7)
    ax2.set_ylabel('Count', fontsize=12)
    ax2.set_title('Deviation Metrics', fontsize=13, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:,.1f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.show()
    
    # Plot 2: Bit-level comparison if available
    if check_bits and results['bit_results']:
        bit_res = results['bit_results']
        bits = bit_res['bits']
        counts1 = bit_res['counts1']
        counts2 = bit_res['counts2']
        deviations = bit_res['deviations']
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        
        # Bit-wise toggle comparison
        ax1 = axes[0]
        x = np.arange(len(bits))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, counts1, width, label=sig1, 
                       color='steelblue', edgecolor='black', alpha=0.7)
        bars2 = ax1.bar(x + width/2, counts2, width, label=sig2,
                       color='coral', edgecolor='black', alpha=0.7)
        
        ax1.set_xlabel('Bit Index', fontsize=12)
        ax1.set_ylabel('Toggle Count', fontsize=12)
        ax1.set_title('Bit-wise Toggle Count Comparison', fontsize=13, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(bits)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Deviation per bit
        ax2 = axes[1]
        colors_dev = ['green' if d == 0 else 'red' for d in deviations]
        bars = ax2.bar(bits, deviations, color=colors_dev, edgecolor='black', alpha=0.7)
        
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax2.set_xlabel('Bit Index', fontsize=12)
        ax2.set_ylabel('Deviation (Signal1 - Signal2)', fontsize=12)
        ax2.set_title('Bit-wise Toggle Deviation', fontsize=13, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        # Add statistics text
        stats_text = (f"Mean Deviation: {bit_res['mean_deviation']:,.2f}\n"
                     f"Mean Abs Deviation: {bit_res['mean_abs_deviation']:,.2f}\n"
                     f"Max Deviation: {bit_res['max_deviation']:,}")
        ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes,
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='wheat', alpha=0.5), fontsize=10)
        
        plt.tight_layout()
        plt.show()

def batch_compare(vcd_file, signal_pairs, check_bits=False, do_plot=False):
    """
    Compare multiple pairs of signals.
    
    Args:
        vcd_file: Path to the VCD file
        signal_pairs: List of tuples [(sig1, sig2), ...]
        check_bits: If True, compare bit-wise toggles
        do_plot: If True, generate plots
    """
    print(f"\nAnalyzing VCD file: {vcd_file}")
    print(f"Comparing {len(signal_pairs)} signal pair(s)...")
    
    for idx, (sig1, sig2) in enumerate(signal_pairs, 1):
        print(f"\n{'#'*70}")
        print(f"# COMPARISON {idx}/{len(signal_pairs)}")
        print(f"{'#'*70}")
        compare_signals(vcd_file, sig1, sig2, check_bits, do_plot)

def main():
    if len(sys.argv) < 4:
        print("Usage: python toggle_comparator.py <vcd_file> <signal1> <signal2> [options]")
        print("\nOptions:")
        print("  --bits    Compare bit-wise toggle counts")
        print("  --plot    Generate comparison plots with deviation visualization")
        print("\nExamples:")
        print("  python toggle_comparator.py simulation.vcd clk reset")
        print("  python toggle_comparator.py simulation.vcd data_bus addr_bus --bits --plot")
        print("\nBatch mode (compare multiple pairs):")
        print("  python toggle_comparator.py simulation.vcd sig1 sig2 sig3 sig4 --bits --plot")
        print("  (This compares sig1 vs sig2, and sig3 vs sig4)")
        return
    
    vcd_file = sys.argv[1]
    check_bits = '--bits' in sys.argv
    do_plot = '--plot' in sys.argv
    
    if do_plot and not PLOT_AVAILABLE:
        print("Warning: matplotlib not installed. Install with: pip install matplotlib numpy")
    
    # Get signal names (excluding flags)
    signals = [arg for arg in sys.argv[2:] if arg not in ['--bits', '--plot']]
    
    if len(signals) < 2:
        print("Error: At least two signals must be specified")
        return
    
    # Pair up signals for comparison
    signal_pairs = []
    for i in range(0, len(signals) - 1, 2):
        if i + 1 < len(signals):
            signal_pairs.append((signals[i], signals[i + 1]))
    
    # If odd number of signals, warn about the last one
    if len(signals) % 2 != 0:
        print(f"Warning: Odd number of signals provided. '{signals[-1]}' will not be compared.")
    
    try:
        if len(signal_pairs) == 1:
            compare_signals(vcd_file, signal_pairs[0][0], signal_pairs[0][1], check_bits, do_plot)
        else:
            batch_compare(vcd_file, signal_pairs, check_bits, do_plot)
    
    except FileNotFoundError:
        print(f"Error: File '{vcd_file}' not found.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()