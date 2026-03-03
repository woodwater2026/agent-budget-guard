#!/usr/bin/env python3
"""
Simple log rotation for Agent Budget Guard.
Rotates usage_log.jsonl when it exceeds size limit.
"""

import os
import shutil
from datetime import datetime

def rotate_logs(log_path="data/usage_log.jsonl", max_size_kb=100):
    """Rotate log file if it exceeds max_size_kb."""
    
    if not os.path.exists(log_path):
        print(f"Log file {log_path} does not exist.")
        return False
    
    # Check file size
    size_bytes = os.path.getsize(log_path)
    size_kb = size_bytes / 1024
    
    if size_kb < max_size_kb:
        print(f"Log size: {size_kb:.1f}KB (under {max_size_kb}KB limit, no rotation needed)")
        return False
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "data/log_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = os.path.join(backup_dir, f"usage_log_{timestamp}.jsonl")
    
    # Rotate the log
    print(f"Rotating log: {size_kb:.1f}KB > {max_size_kb}KB limit")
    print(f"Backing up to: {backup_path}")
    
    # Copy current log to backup
    shutil.copy2(log_path, backup_path)
    
    # Truncate current log (keep last 100 lines for continuity)
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    # Keep last 100 entries
    if len(lines) > 100:
        keep_lines = lines[-100:]
        with open(log_path, 'w') as f:
            f.writelines(keep_lines)
        print(f"Kept last 100 entries ({len(keep_lines)} lines)")
    else:
        # Clear the file
        open(log_path, 'w').close()
        print("Cleared log file")
    
    # Compress old backups (optional)
    print("Log rotation complete")
    return True

def cleanup_old_backups(backup_dir="data/log_backups", keep_days=30):
    """Remove backup files older than keep_days."""
    
    if not os.path.exists(backup_dir):
        return
    
    now = datetime.now().timestamp()
    cutoff = now - (keep_days * 24 * 3600)
    
    removed = 0
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath):
            file_time = os.path.getmtime(filepath)
            if file_time < cutoff:
                os.remove(filepath)
                removed += 1
                print(f"Removed old backup: {filename}")
    
    if removed > 0:
        print(f"Cleaned up {removed} old backup files")

if __name__ == "__main__":
    print("Agent Budget Guard Log Rotation")
    print("=" * 40)
    
    log_path = "data/usage_log.jsonl"
    
    # Rotate if needed
    rotated = rotate_logs(log_path, max_size_kb=50)  # 50KB limit
    
    # Cleanup old backups
    cleanup_old_backups(keep_days=7)  # Keep 7 days of backups
    
    if not rotated:
        print("No rotation needed at this time.")