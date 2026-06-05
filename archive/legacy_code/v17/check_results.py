import csv
from pathlib import Path
from collections import Counter

csv_path = Path('batch_results/summary_20251017_123810.csv')

status_counts = Counter()
total_batches = 0
total_files = 0
success_batches = []
failed_batches = []
partial_batches = []

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    for row in reader:
        total_batches += 1
        status_counts[row['status']] += 1
        total_files += int(row['files_processed'])

        success_rate = float(row['success_rate'])

        if row['status'] == 'success':
            success_batches.append((row['batch_name'], row['files_processed']))
        elif row['status'] == 'failed':
            failed_batches.append((row['batch_name'], success_rate, row['files_processed']))
        elif row['status'] == 'partial':
            partial_batches.append((row['batch_name'], success_rate, row['files_processed']))

print("=" * 80)
print("BATCH PROCESSING SUMMARY")
print("=" * 80)
print(f"Total batches: {total_batches}")
print(f"Total files: {total_files}")
print(f"\nStatus Distribution:")
for status, count in sorted(status_counts.items()):
    pct = (count / total_batches * 100)
    print(f"  {status:12s}: {count:4d} ({pct:5.1f}%)")

print(f"\nSuccess batches: {len(success_batches)}")
if success_batches:
    print("  Examples:")
    for name, files in success_batches[:3]:
        print(f"    - {name} ({files} files)")

print(f"\nPartial batches: {len(partial_batches)}")
if partial_batches:
    print("  Top 3 by success rate:")
    partial_batches.sort(key=lambda x: x[1], reverse=True)
    for name, rate, files in partial_batches[:3]:
        print(f"    - {name}: {rate:.1f}% ({files} files)")

print(f"\nFailed batches: {len(failed_batches)}")
if failed_batches:
    print("  Examples with some success:")
    failed_batches.sort(key=lambda x: x[1], reverse=True)
    for name, rate, files in failed_batches[:5]:
        if rate > 0:
            print(f"    - {name}: {rate:.1f}% ({files} files)")
