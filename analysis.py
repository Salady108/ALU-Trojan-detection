#!/usr/bin/env python3
"""
VCD (Value Change Dump) Toggle Counter
Reads a VCD file and counts the number of toggles for each signal.

Installation for plotting:
    pip install matplotlib
"""

import re
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('TkAgg')  # Use TkAgg backend for display
    PLOT_AVAILABLE = True
except ImportError:
    PLOT_AVAILABLE = False

def parse_vcd(filename, filter_signals=None, track_bits=False):
    """
    Parse a VCD file and count toggles for each signal.
    
    Args:
        filename: Path to the VCD file
        filter_signals: List of signal name patterns to filter (optional)
        track_bits: If True, track individual bit toggles for multi-bit signals
        
    Returns:
        Dictionary mapping signal names to toggle counts
    """
    # Map identifier codes to signal names and widths
    id_to_signal = {}
    id_to_width = {}
    # Track previous values for each signal
    prev_values = {}
    # Count toggles for each signal
    toggle_counts = defaultdict(int)
    # Count toggles for individual bits (if track_bits=True)
    bit_toggle_counts = defaultdict(lambda: defaultdict(int))
    
    in_definitions = True
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Parse variable definitions in the header
            if in_definitions:
                if line.startswith('$var'):
                    # Example: $var wire 1 ! clk $end
                    parts = line.split()
                    if len(parts) >= 5:
                        var_type = parts[1]
                        width = int(parts[2])
                        identifier = parts[3]
                        signal_name = parts[4]
                        id_to_signal[identifier] = signal_name
                        id_to_width[identifier] = width
                
                elif line.startswith('$enddefinitions'):
                    in_definitions = False
                    
            # Parse value changes
            else:
                # Single-bit value change: 0! or 1! or x! or z!
                match = re.match(r'^([01xzXZ])(.+)$', line)
                if match:
                    value = match.group(1)
                    identifier = match.group(2)
                    
                    if identifier in id_to_signal:
                        signal = id_to_signal[identifier]
                        
                        # Skip if filtering and signal doesn't match
                        if filter_signals:
                            if not any(filt in signal for filt in filter_signals):
                                continue
                        
                        # Check if value changed (toggle)
                        if signal in prev_values:
                            # Only count as toggle if transitioning between 0 and 1
                            if (prev_values[signal] in ['0', '1'] and 
                                value in ['0', '1'] and 
                                prev_values[signal] != value):
                                toggle_counts[signal] += 1
                        
                        prev_values[signal] = value
                
                # Multi-bit value change: b1010 identifier
                elif line.startswith('b'):
                    parts = line.split()
                    if len(parts) >= 2:
                        value = parts[0][1:]  # Remove 'b' prefix
                        identifier = parts[1]
                        
                        if identifier in id_to_signal:
                            signal = id_to_signal[identifier]
                            
                            # Skip if filtering and signal doesn't match
                            if filter_signals:
                                if not any(filt in signal for filt in filter_signals):
                                    continue
                            
                            if signal in prev_values and prev_values[signal] != value:
                                toggle_counts[signal] += 1
                                
                                # Track individual bit toggles if requested
                                if track_bits:
                                    prev_val = prev_values[signal]
                                    # Pad with zeros if needed
                                    width = id_to_width.get(identifier, max(len(value), len(prev_val)))
                                    prev_val = prev_val.zfill(width)
                                    value_padded = value.zfill(width)
                                    
                                    # Check each bit
                                    for bit_idx in range(len(value_padded)):
                                        if bit_idx < len(prev_val):
                                            prev_bit = prev_val[-(bit_idx+1)]
                                            curr_bit = value_padded[-(bit_idx+1)]
                                            if (prev_bit in ['0', '1'] and 
                                                curr_bit in ['0', '1'] and 
                                                prev_bit != curr_bit):
                                                bit_toggle_counts[signal][bit_idx] += 1
                            
                            prev_values[signal] = value
    
    return toggle_counts, id_to_signal, bit_toggle_counts

def plot_toggle_counts(toggle_counts, title="Signal Toggle Counts"):
    """Plot toggle counts as a bar chart."""
    if not PLOT_AVAILABLE:
        print("\nMatplotlib not available. Install with: pip install matplotlib")
        return
    
    if not toggle_counts:
        print("\nNo data to plot.")
        return
    
    # Sort by toggle count (descending)
    sorted_data = sorted(toggle_counts.items(), key=lambda x: x[1], reverse=True)
    signals = [s for s, _ in sorted_data]
    counts = [c for _, c in sorted_data]
    
    # Limit to top 20 signals if too many
    if len(signals) > 20:
        signals = signals[:20]
        counts = counts[:20]
        title += " (Top 20)"
    
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(signals)), counts, color='steelblue', edgecolor='black')
    plt.xlabel('Signal', fontsize=12)
    plt.ylabel('Toggle Count', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xticks(range(len(signals)), signals, rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()

def plot_bit_toggles(bit_toggle_counts, signal_name=None):
    """Plot individual bit toggle counts for multi-bit signals."""
    if not PLOT_AVAILABLE:
        print("\nMatplotlib not available. Install with: pip install matplotlib")
        return
    
    if not bit_toggle_counts:
        print("\nNo bit toggle data available.")
        return
    
    # If specific signal requested
    if signal_name:
        if signal_name not in bit_toggle_counts:
            print(f"\nNo bit toggle data for signal: {signal_name}")
            return
        signals_to_plot = {signal_name: bit_toggle_counts[signal_name]}
    else:
        # Plot all signals with bit data
        signals_to_plot = bit_toggle_counts
    
    num_signals = len(signals_to_plot)
    
    # Create subplots
    if num_signals == 1:
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        axes = [ax]
    else:
        # Multiple subplots
        cols = min(2, num_signals)
        rows = (num_signals + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(12, 4*rows))
        if num_signals == 2:
            axes = axes.flatten() if hasattr(axes, 'flatten') else [axes[0], axes[1]]
        elif num_signals > 2:
            axes = axes.flatten()
        else:
            axes = [axes]
    
    colors = ['coral', 'steelblue', 'lightgreen', 'gold', 'plum', 'salmon']
    
    for idx, (signal, bit_counts) in enumerate(sorted(signals_to_plot.items())):
        if idx >= len(axes):
            break
            
        bits = sorted(bit_counts.keys())
        counts = [bit_counts[b] for b in bits]
        
        ax = axes[idx]
        ax.bar(bits, counts, color=colors[idx % len(colors)], edgecolor='black', alpha=0.7)
        ax.set_xlabel('Bit Index', fontsize=10)
        ax.set_ylabel('Toggle Count', fontsize=10)
        ax.set_title(f'{signal}', fontsize=11, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    # Hide empty subplots
    for idx in range(num_signals, len(axes)):
        axes[idx].set_visible(False)
    
    plt.tight_layout()
    plt.show()

def plot_bit_comparison(bit_toggle_counts):
    """Plot bit toggle counts for all signals on the same chart for comparison."""
    if not PLOT_AVAILABLE:
        print("\nMatplotlib not available. Install with: pip install matplotlib")
        return
    
    if not bit_toggle_counts:
        print("\nNo bit toggle data available.")
        return
    
    plt.figure(figsize=(14, 7))
    
    colors = ['coral', 'steelblue', 'lightgreen', 'gold', 'plum', 'salmon', 'cyan', 'orange']
    bar_width = 0.8 / len(bit_toggle_counts)
    
    # Get all unique bit indices across all signals
    all_bits = set()
    for bit_counts in bit_toggle_counts.values():
        all_bits.update(bit_counts.keys())
    all_bits = sorted(all_bits)
    
    # Plot each signal's bits
    for idx, (signal, bit_counts) in enumerate(sorted(bit_toggle_counts.items())):
        counts = [bit_counts.get(b, 0) for b in all_bits]
        positions = [b + idx * bar_width for b in all_bits]
        plt.bar(positions, counts, bar_width, 
                label=signal, color=colors[idx % len(colors)], 
                edgecolor='black', alpha=0.7)
    
    plt.xlabel('Bit Index', fontsize=12)
    plt.ylabel('Toggle Count', fontsize=12)
    plt.title('Bit-wise Toggle Comparison Across Signals', fontsize=14, fontweight='bold')
    plt.legend(loc='best')
    plt.grid(axis='y', alpha=0.3)
    plt.xticks(all_bits)
    plt.tight_layout()
    plt.show()

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python vcd_toggle_counter.py <vcd_file> [options] [signal1] [signal2] ...")
        print("\nOptions:")
        print("  --bits    Show toggle counts for individual bits of multi-bit signals")
        print("  --plot    Generate bar chart of toggle counts")
        print("\nExamples:")
        print("  python vcd_toggle_counter.py simulation.vcd")
        print("  python vcd_toggle_counter.py simulation.vcd clk reset")
        print("  python vcd_toggle_counter.py simulation.vcd --bits data_bus")
        print("  python vcd_toggle_counter.py simulation.vcd --plot")
        print("  python vcd_toggle_counter.py simulation.vcd --bits --plot data_bus")
        return
    
    # Check for flags in all arguments
    track_bits = '--bits' in sys.argv
    do_plot = '--plot' in sys.argv
    
    # Get all arguments except flags
    args = [arg for arg in sys.argv[1:] if arg not in ['--bits', '--plot']]
    
    if not args:
        print("Error: VCD file not specified")
        return
    
    vcd_file = args[0]
    filter_signals = args[1:] if len(args) > 1 else None
    
    print(f"Analyzing VCD file: {vcd_file}")
    if filter_signals:
        print(f"Filtering for signals containing: {', '.join(filter_signals)}")
    if track_bits:
        print("Tracking individual bit toggles")
    if do_plot and not PLOT_AVAILABLE:
        print("Warning: matplotlib not installed. Install with: pip install matplotlib")
    print("-" * 60)
    
    try:
        toggle_counts, signals, bit_toggle_counts = parse_vcd(vcd_file, filter_signals, track_bits)
        
        if not toggle_counts and filter_signals:
            print(f"\nNo signals found matching: {', '.join(filter_signals)}")
            print("\nAvailable signals:")
            for sig in sorted(signals.values())[:20]:
                print(f"  {sig}")
            if len(signals) > 20:
                print(f"  ... and {len(signals) - 20} more")
            return
        
        # Sort by signal name for consistent output
        sorted_signals = sorted(toggle_counts.items())
        
        print(f"\n{'Signal Name':<30} {'Toggle Count':>15}")
        print("=" * 60)
        
        for signal, count in sorted_signals:
            print(f"{signal:<30} {count:>15,}")
        
        # Show individual bit toggles if requested
        if track_bits and bit_toggle_counts:
            print("\n" + "=" * 60)
            print("Individual Bit Toggle Counts:")
            print("=" * 60)
            
            for signal in sorted(bit_toggle_counts.keys()):
                print(f"\n{signal}:")
                bit_counts = bit_toggle_counts[signal]
                for bit_idx in sorted(bit_counts.keys()):
                    print(f"  Bit[{bit_idx}]: {bit_counts[bit_idx]:,} toggles")
        
        print("\n" + "=" * 60)
        print(f"Total signals analyzed: {len(signals)}")
        print(f"Signals with toggles: {len(toggle_counts)}")
        
        if toggle_counts:
            total_toggles = sum(toggle_counts.values())
            print(f"Total toggles: {total_toggles:,}")
        
        # Generate plots if requested
        if do_plot and toggle_counts:
            print("\nGenerating plots...")
            
            # Plot signal-level toggles
            plot_toggle_counts(toggle_counts, "Signal Toggle Counts")
            
            # If tracking bits and there's bit data, plot bit-wise comparison
            if track_bits and bit_toggle_counts:
                # Individual subplots for each signal
                plot_bit_toggles(bit_toggle_counts)
                
                # Comparison chart with all signals
                if len(bit_toggle_counts) > 1:
                    plot_bit_comparison(bit_toggle_counts)
    
    except FileNotFoundError:
        print(f"Error: File '{vcd_file}' not found.")
    except Exception as e:
        print(f"Error parsing VCD file: {e}")

if __name__ == "__main__":
    main()